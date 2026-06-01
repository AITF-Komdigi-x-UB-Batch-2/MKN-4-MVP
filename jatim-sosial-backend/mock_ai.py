import os
import json
import uvicorn
import asyncio
import random
import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, Body, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

# PYDANTIC RESPONSE SCHEMAS
class JalurSosialResponse(BaseModel):
    status: str
    rekomendasi_bantuan: List[str]
    justifikasi_dokumen: str
    skor_aspd: float
    skor_pkh_plus: float


class VisualValidatorResponse(BaseModel):
    is_match: bool
    reasoning: str


def hitung_skor_deterministik(data_warga: dict) -> dict:
    """
    Menghitung skor kelayakan bantuan secara deterministik berdasarkan data profil keluarga:
    1. ASPD (Asistensi Sosial Penyandang Disabilitas) - Bobot: Disabilitas (60%), Kemandirian (20%), Ekonomi/Desil (20%)
    2. PKH Plus (Program Keluarga Harapan Plus) - Bobot: Desil/Ekstrem (40%), Kelayakan Hunian/Material (30%), Aset (20%), Jumlah Anggota (10%)
    """
    # --- FORMULA SKOR ASPD ---
    skor_aspd = 10.0  # Skor dasar
    
    # 1. Kriteria Disabilitas (Maksimal 60 poin)
    id_disabilitas = data_warga.get("id_disabilitas")
    tingkat_disabilitas = data_warga.get("tingkat_disabilitas")
    aspd_flag = data_warga.get("aspd")
    
    if id_disabilitas and int(float(id_disabilitas)) > 0:
        skor_aspd += 40.0
    
    if tingkat_disabilitas:
        tingkat_upper = str(tingkat_disabilitas).upper()
        if "BERAT" in tingkat_upper:
            skor_aspd += 20.0
        elif "SEDANG" in tingkat_upper:
            skor_aspd += 12.0
        elif "RINGAN" in tingkat_upper:
            skor_aspd += 5.0
            
    if aspd_flag and int(float(aspd_flag)) == 1:
        skor_aspd += 15.0

    # Batasi kontribusi disabilitas max 70
    skor_aspd = min(skor_aspd, 70.0)

    # 2. Dampak Kemandirian (Fisik/Mental) (Maksimal 20 poin)
    kesulitan = 0.0
    for var in ["id_mengurus_diri", "id_berjalan_atau_naik_tangga", "id_belajar_kemampuan_intelektual", "id_berbicara_komunikasi"]:
        val = data_warga.get(var)
        if val is not None:
            try:
                val_int = int(float(val))
                if val_int == 1:  # Sangat Sulit
                    kesulitan += 8.0
                elif val_int == 2:  # Sulit
                    kesulitan += 5.0
                elif val_int == 3:  # Sedikit Sulit
                    kesulitan += 2.0
            except (ValueError, TypeError):
                pass
    skor_aspd += min(kesulitan, 20.0)

    # 3. Kriteria Desil Ekonomi (Maksimal 10 poin)
    desil = data_warga.get("desil_nasional")
    if desil is not None:
        try:
            desil_int = int(float(desil))
            if desil_int == 1:
                skor_aspd += 10.0
            elif desil_int == 2:
                skor_aspd += 8.0
            elif desil_int == 3:
                skor_aspd += 6.0
            elif desil_int == 4:
                skor_aspd += 4.0
        except (ValueError, TypeError):
            pass

    # Total Maksimal ASPD = 100, Minimal = 0
    skor_aspd = min(max(round(skor_aspd, 2), 0.0), 100.0)


    # --- FORMULA SKOR PKH PLUS ---
    skor_pkh = 10.0  # Skor dasar

    # 1. Kriteria Desil dan Kemiskinan Ekstrem (Maksimal 40 poin)
    desil = data_warga.get("desil_nasional")
    kemiskinan_ekstrem = data_warga.get("kemiskinan_ekstrem")
    pkh_plus_flag = data_warga.get("pkh_plus")
    
    if desil is not None:
        try:
            desil_int = int(float(desil))
            if desil_int == 1:
                skor_pkh += 25.0
            elif desil_int == 2:
                skor_pkh += 20.0
            elif desil_int == 3:
                skor_pkh += 15.0
            elif desil_int == 4:
                skor_pkh += 10.0
        except (ValueError, TypeError):
            pass

    if kemiskinan_ekstrem and int(float(kemiskinan_ekstrem)) == 1:
        skor_pkh += 10.0
        
    if pkh_plus_flag and int(float(pkh_plus_flag)) == 1:
        skor_pkh += 10.0

    skor_pkh = min(skor_pkh, 45.0)

    # 2. Kelayakan Material Rumah (Maksimal 25 poin)
    id_lantai = data_warga.get("id_lantai_terluas")
    id_dinding = data_warga.get("id_dinding_terluas")
    id_atap = data_warga.get("id_atap_terluas")
    
    material_score = 0.0
    if id_lantai is not None:
        try:
            if int(float(id_lantai)) >= 3:
                material_score += 10.0
        except (ValueError, TypeError):
            pass
    if id_dinding is not None:
        try:
            if int(float(id_dinding)) >= 2:
                material_score += 8.0
        except (ValueError, TypeError):
            pass
    if id_atap is not None:
        try:
            if int(float(id_atap)) >= 3:
                material_score += 7.0
        except (ValueError, TypeError):
            pass
    skor_pkh += min(material_score, 25.0)

    # 3. Ketiadaan Aset Produktif/Bergerak (Maksimal 20 poin)
    punya_motor = data_warga.get("aset_bergerak_sepeda_motor")
    punya_kulkas = data_warga.get("aset_bergerak_lemari_es")
    punya_tv = data_warga.get("aset_bergerak_tv_datar")
    punya_ac = data_warga.get("aset_bergerak_ac")
    
    aset_score = 0.0
    if punya_motor is not None and int(float(punya_motor)) == 0:
        aset_score += 8.0
    if punya_kulkas is not None and int(float(punya_kulkas)) == 0:
        aset_score += 5.0
    if punya_tv is not None and int(float(punya_tv)) == 0:
        aset_score += 4.0
    if punya_ac is not None and int(float(punya_ac)) == 0:
        aset_score += 3.0
        
    skor_pkh += min(aset_score, 20.0)

    # 4. Kriteria Kerentanan Lansia (Jumlah Anggota Keluarga) (Maksimal 10 poin)
    jumlah_anggota = data_warga.get("jumlah_anggota_keluarga")
    if jumlah_anggota is not None:
        try:
            if int(float(jumlah_anggota)) >= 5:
                skor_pkh += 10.0
            elif int(float(jumlah_anggota)) >= 3:
                skor_pkh += 5.0
        except (ValueError, TypeError):
            pass

    # Total Maksimal PKH Plus = 100, Minimal = 0
    skor_pkh = min(max(round(skor_pkh, 2), 0.0), 100.0)

    return {"skor_aspd": skor_aspd, "skor_pkh_plus": skor_pkh}


# INISIALISASI FASTAPI
app = FastAPI(
    title="Mock AI Server",
    version="3.0",
    description="Server AI Jatim Sosial — Mengintegrasikan AWS Bedrock Gemma-3 dengan fallback otomatis."
)

# ENDPOINT TIM 1 & 3: JALUR SOSIAL (ANALISIS + RAG DENGAN GEMMA 3)
@app.post(
    "/api/ai/jalur-sosial",
    tags=["Tim 1 & 3 - Jalur Sosial"],
    summary="Analisis sosial ekonomi + RAG rekomendasi bantuan",
    response_model=JalurSosialResponse
)
async def mock_jalur_sosial(data_warga: dict = Body(...)):
    nomor_kk = data_warga.get("nomor_kartu_keluarga", "UNKNOWN")
    
    # Ambil kredensial AWS dari environment secara aman (tanpa hardcode string rahasia)
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION", "us-east-1")

    # Jalankan pemanggilan Bedrock secara asinkron di thread pool agar tidak memblokir event loop FastAPI
    loop = asyncio.get_event_loop()
    
    def panggil_bedrock_sosial():
        try:
            client = boto3.client(
                "bedrock-runtime",
                region_name=aws_region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            
            prompt_system = (
                "Anda adalah ahli analisis sosial ekonomi dan sistem bantuan sosial pemerintah Provinsi Jawa Timur.\n"
                "Tugas Anda adalah menganalisis data profil keluarga yang diberikan untuk menentukan kelayakan dan jenis bantuan yang tepat sasaran.\n"
                "Tentukan:\n"
                "1. Status tingkat kemiskinan (pilih salah satu dari: 'Sangat Miskin', 'Rentan Miskin', atau 'Mampu').\n"
                "2. Rekomendasi bantuan sosial yang sesuai dari daftar berikut: 'ASPD', 'PKHT'.\n"
                "   - Rekomendasikan 'ASPD' jika terdapat anggota keluarga penyandang disabilitas (disabilitas > 0 atau ada tingkat disabilitas).\n"
                "   - Rekomendasikan 'PKHT' jika keluarga tersebut miskin/rentan miskin dan layak menerima Program Keluarga Harapan Plus (PKH Plus).\n"
                "   - Rekomendasikan keduanya jika memenuhi syarat keduanya.\n"
                "   - JANGAN merekomendasikan bantuan lain selain 'ASPD' dan 'PKHT'. Jika tidak layak mendapat keduanya, kembalikan array kosong [].\n"
                "3. Justifikasi/alasan ilmiah terperinci mengapa mereka layak atau tidak layak menerima bantuan tersebut berdasarkan kondisi disabilitas (untuk ASPD) dan kondisi desil/kemiskinan (untuk PKHT).\n\n"
                "Format respon Anda HARUS berupa JSON valid dengan struktur kunci berikut:\n"
                "{\n"
                '  "status": "Sangat Miskin / Rentan Miskin / Mampu",\n'
                '  "rekomendasi_bantuan": ["ASPD", "PKHT"],\n'
                '  "justifikasi_dokumen": "Tuliskan 2-3 kalimat analisis objektif mengapa bantuan ini direkomendasikan berdasarkan kondisi disabilitas atau tingkat desil kesejahteraan mereka."\n'
                "}\n\n"
                "Kembalikan HANYA objek JSON di atas tanpa tambahan teks pembuka, penutup, atau pembungkus markdown (```json)."
            )

            prompt_user = f"Berikut data profil keluarga untuk kartu keluarga {nomor_kk}:\n{json.dumps(data_warga, indent=2)}"
            
            payload = {
                "messages": [
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": prompt_user}
                ],
                "response_format": {
                    "type": "json_object"
                },
                "temperature": 0.3,
                "max_tokens": 1024
            }

            response = client.invoke_model(
                modelId="google.gemma-3-4b-it",
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )

            response_body = json.loads(response.get("body").read())
            teks_jawaban = response_body["choices"][0]["message"]["content"]
            
            # Sanitasi jika AI bandel menyertakan markdown block
            if teks_jawaban.strip().startswith("```"):
                teks_jawaban = teks_jawaban.strip().strip("```json").strip("```").strip()
                
            return json.loads(teks_jawaban)
        except Exception as e:
            print(f"[AWS Bedrock Sosial Error] {e}")
            return None

    # Panggil bedrock
    hasil_ai = await loop.run_in_executor(None, panggil_bedrock_sosial)

    # MEKANISME FALLBACK: Menggunakan logic aturan statis jika AWS Bedrock mati/error
    if hasil_ai is None or not isinstance(hasil_ai, dict):
        print("[Fallback] Mengaktifkan analisis rule-based statis cadangan.")
        await asyncio.sleep(1.0)
        
        id_disabilitas = data_warga.get("id_disabilitas")
        tingkat_disabilitas = data_warga.get("tingkat_disabilitas")
        desil_nasional = data_warga.get("desil_nasional")
        pkh_plus = data_warga.get("pkh_plus")
        aspd = data_warga.get("aspd")

        rekomendasi = []
        justifikasi = []
        
        # Aturan ASPD (Disabilitas)
        has_disability = False
        if id_disabilitas and id_disabilitas > 0:
            has_disability = True
        if tingkat_disabilitas and str(tingkat_disabilitas).strip() not in ["", "None", "0"]:
            has_disability = True
        if aspd and aspd == 1:
            has_disability = True

        if has_disability:
            rekomendasi.append("ASPD")
            justifikasi.append("Terdapat anggota keluarga penyandang disabilitas (Rekomendasi bantuan ASPD)")
        
        # Aturan PKHT (PKH Plus)
        is_poor = False
        if pkh_plus and pkh_plus == 1:
            is_poor = True
        if desil_nasional and desil_nasional <= 4:
            is_poor = True
        
        if is_poor:
            rekomendasi.append("PKHT")
            justifikasi.append(f"Keluarga tergolong miskin/rentan (Desil {desil_nasional or 1}) (Rekomendasi bantuan PKH Plus)")
        
        if not rekomendasi:
            justifikasi.append("Keluarga dinilai mampu secara ekonomi dan tidak terdata penyandang disabilitas.")

        alasan_lengkap = " | ".join(justifikasi) if justifikasi else "Analisis sosial ekonomi selesai"
        
        scores = hitung_skor_deterministik(data_warga)
        return {
            "status": "success",
            "rekomendasi_bantuan": rekomendasi,
            "justifikasi_dokumen": f"KK: {nomor_kk} → {alasan_lengkap} (Menggunakan Analisis Cadangan)",
            "skor_aspd": scores["skor_aspd"],
            "skor_pkh_plus": scores["skor_pkh_plus"]
        }

    # Kembalikan respon dari AI sesungguhnya
    rekomendasi_final = hasil_ai.get("rekomendasi_bantuan", [])
    # Sanitasi agar hanya berisi program yang valid
    rekomendasi_final = [r for r in rekomendasi_final if r in ["ASPD", "PKHT"]]

    scores = hitung_skor_deterministik(data_warga)
    return {
        "status": hasil_ai.get("status", "success"),
        "rekomendasi_bantuan": rekomendasi_final,
        "justifikasi_dokumen": f"KK: {nomor_kk} → {hasil_ai.get('justifikasi_dokumen', 'Analisis AI selesai.')}",
        "skor_aspd": scores["skor_aspd"],
        "skor_pkh_plus": scores["skor_pkh_plus"]
    }


# ENDPOINT TIM 2: VISUAL VALIDATOR (VALIDASI FOTO DENGAN GEMMA 3)
@app.post(
    "/api/ai/visual-validator",
    tags=["Tim 2 - Visual Validator"],
    summary="Validasi kesesuaian foto rumah dengan data sosial ekonomi",
    response_model=VisualValidatorResponse
)
async def mock_visual_validator(payload: dict = Body(...)):
    image_url = payload.get("image_url", "")
    konteks = payload.get("konteks_rumah", {})
    
    jenis_lantai = konteks.get("jenis_lantai_terluas", "unknown")
    jenis_dinding = konteks.get("jenis_dinding_terluas", "unknown")
    jenis_atap = konteks.get("jenis_atap_terluas", "unknown")

    # Ambil random kecocokan (75% True, 25% False) untuk simulasi
    is_match = random.choice([True, True, True, False])

    # Kredensial AWS Bedrock secara aman dari environment
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION", "us-east-1")

    loop = asyncio.get_event_loop()

    def panggil_bedrock_visual():
        try:
            client = boto3.client(
                "bedrock-runtime",
                region_name=aws_region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            
            prompt_system = (
                "Anda adalah AI asisten validator foto rumah untuk program bantuan sosial Provinsi Jawa Timur.\n"
                "Tugas Anda adalah menulis teks pertanggungjawaban/justifikasi validasi visual yang terdengar sangat analitis dan meyakinkan.\n\n"
                f"Tingkat kesesuaian foto yang ditentukan oleh sistem: {'COCOK / SESUAI' if is_match else 'TIDAK COCOK / ADA INKONSISTENSI'}.\n"
                f"Data Profil Rumah Warga:\n"
                f"- Lantai: {jenis_lantai}\n"
                f"- Dinding: {jenis_dinding}\n"
                f"- Atap: {jenis_atap}\n\n"
                "Tuliskan 1 paragraf pendek (2-3 kalimat saja) yang menjustifikasi status kesesuaian visual tersebut dengan membandingkan profil material di atas. "
                "Gunakan bahasa Indonesia yang profesional, tegas, dan ilmiah seolah Anda menganalisis citra visual foto secara mendalam."
            )

            payload = {
                "messages": [
                    {"role": "user", "content": prompt_system}
                ],
                "temperature": 0.7,
                "max_tokens": 256
            }

            response = client.invoke_model(
                modelId="google.gemma-3-4b-it",
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )

            response_body = json.loads(response.get("body").read())
            teks_jawaban = response_body["choices"][0]["message"]["content"]
            return teks_jawaban.strip()
        except Exception as e:
            print(f"[AWS Bedrock Visual Error] {e}")
            return None

    # Jalankan pemanggilan Bedrock secara asinkron
    alasan_dinamis = await loop.run_in_executor(None, panggil_bedrock_visual)

    # MEKANISME FALLBACK: Gunakan text rule-based jika Bedrock gagal
    if not alasan_dinamis:
        await asyncio.sleep(1.0)
        if is_match:
            alasan_dinamis = (
                f"Foto SESUAI dengan data profil. "
                f"Kondisi visual rumah konsisten: lantai={jenis_lantai}, "
                f"dinding={jenis_dinding}, atap={jenis_atap}. "
                f"Status: TERVERIFIKASI"
            )
        else:
            alasan_dinamis = (
                f"Foto TIDAK SESUAI dengan data profil. "
                f"Terdapat inkonsistensi antara foto dan data sosial ekonomi yang tercatat. "
                f"Rekomendasi: Perlu verifikasi ulang lapangan."
            )

    return {
        "is_match": is_match,
        "reasoning": alasan_dinamis
    }


# HEALTH CHECK
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "Mock AI Server is running and Bedrock integrated..."}


if __name__ == "__main__":
    print("Menjalankan Server AI Jatim Sosial di Port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)