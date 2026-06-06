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
    # ASPD hanya dihitung jika warga memiliki disabilitas (id_disabilitas > 0)
    id_disabilitas = data_warga.get("id_disabilitas")
    try:
        id_disab_val = int(float(id_disabilitas)) if id_disabilitas is not None else 0
    except (ValueError, TypeError):
        id_disab_val = 0

    if id_disab_val <= 0:
        skor_aspd = 0.0
    else:
        skor_aspd = 10.0  # Skor dasar
        
        # 1. Kriteria Disabilitas (Maksimal 60 poin)
        skor_aspd += 40.0
        
        tingkat_disabilitas = data_warga.get("tingkat_disabilitas")
        if tingkat_disabilitas:
            tingkat_upper = str(tingkat_disabilitas).upper()
            if "BERAT" in tingkat_upper:
                skor_aspd += 20.0
            elif "SEDANG" in tingkat_upper:
                skor_aspd += 12.0
            elif "RINGAN" in tingkat_upper:
                skor_aspd += 5.0
                
        aspd_flag = data_warga.get("aspd")
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
        
        # 1. Cek Disabilitas
        has_disability = False
        if id_disabilitas and id_disabilitas > 0:
            has_disability = True
        if tingkat_disabilitas and str(tingkat_disabilitas).strip() not in ["", "None", "0"]:
            has_disability = True
        if aspd and aspd == 1:
            has_disability = True

        # 2. Cek Kemiskinan
        is_poor = False
        if pkh_plus and pkh_plus == 1:
            is_poor = True
        if desil_nasional and desil_nasional <= 4:
            is_poor = True

        # 3. Ambil Umur
        umur = data_warga.get("umur_2026") or data_warga.get("umur")
        if umur is None:
            tgl = data_warga.get("tanggal_lahir")
            if tgl:
                try:
                    tahun_lahir = int(str(tgl).split("-")[0].strip())
                    import datetime
                    umur = datetime.datetime.now().year - tahun_lahir
                except Exception:
                    pass
        if umur is None:
            umur = 0

        # 4. Filter Aturan Seleksi Ketat (Mutual Exclusive Usia)
        # PKH Plus: lansia >= 70 tahun
        if is_poor and umur >= 70:
            rekomendasi.append("PKHT")
            justifikasi.append(f"Keluarga tergolong miskin/rentan (Desil {desil_nasional or 1}) dan usia memenuhi syarat lansia ({umur} tahun >= 70)")
        
        # ASPD: usia 6 bulan - 60 tahun (0.5 <= umur <= 60)
        if has_disability and (0.5 <= umur <= 60):
            rekomendasi.append("ASPD")
            justifikasi.append(f"Terdapat disabilitas/bed ridden dan usia memenuhi syarat ASPD ({umur} tahun berada di rentang 6 bulan - 60 tahun)")
        
        if not rekomendasi:
            justifikasi.append(f"Keluarga tidak memenuhi syarat seleksi (Umur: {umur} tahun, Desil: {desil_nasional or 10}, Disabilitas: {has_disability})")

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


# --- OPENAI / RUNPOD COMPATIBLE CHAT COMPLETIONS ENDPOINT (DYNAMIC MOCK) ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    response_format: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048

def extract_from_prompt(prompt: str) -> dict:
    data = {}
    if not prompt:
        return data
    lines = prompt.split("\n")
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip().replace("-", "").strip().lower()
            val = parts[1].strip()
            
            # Match keys
            if "nik" in key:
                data["nik"] = val
            elif "nama" in key:
                data["nama"] = val
            elif "desil nasional" in key:
                try:
                    data["desil_nasional"] = int(float(val))
                except (ValueError, TypeError):
                    data["desil_nasional"] = 4
            elif "skor pkh plus" in key:
                try:
                    data["skor_pkh_plus"] = float(val)
                except (ValueError, TypeError):
                    data["skor_pkh_plus"] = 0.0
            elif "skor aspd" in key:
                try:
                    data["skor_aspd"] = float(val)
                except (ValueError, TypeError):
                    data["skor_aspd"] = 0.0
            elif "umur" in key:
                try:
                    cleaned_val = val.split(" ")[0].strip()
                    data["umur"] = int(float(cleaned_val))
                except (ValueError, TypeError):
                    data["umur"] = 0
            elif "penglihatan" in key:
                data["id_penglihatan"] = val
            elif "pendengaran" in key:
                data["id_pendengaran"] = val
            elif "berjalan/tangga" in key:
                data["id_berjalan_atau_naik_tangga"] = val
            elif "tangan/jari" in key:
                data["id_menggunakan_tangan_jari"] = val
            elif "belajar/intelektual" in key:
                data["id_belajar_kemampuan_intelektual"] = val
            elif "pengendalian perilaku" in key:
                data["id_pengendalian_perilaku"] = val
            elif "bicara/komunikasi" in key:
                data["id_berbicara_komunikasi"] = val
            elif "mengurus diri" in key:
                data["id_mengurus_diri"] = val
            elif "memori/konsentrasi" in key:
                data["id_mengingat_berkonsentrasi"] = val
            elif "kesedihan/depresi" in key:
                data["id_kesedihan_depresi"] = val
    return data

@app.post(
    "/v1/chat/completions",
    tags=["OpenAI Compatible completions"],
    summary="Mock API OpenAI Chat Completions secara dinamis"
)
async def chat_completions(req: ChatCompletionRequest):
    # Cari pesan dari user
    user_content = ""
    for msg in req.messages:
        if msg.role == "user":
            user_content = msg.content
            break
            
    # Ekstrak data warga dari prompt
    data = extract_from_prompt(user_content)
    umur = data.get("umur", 0)
    
    # 1. Cek Kelayakan Disabilitas (ASPD)
    has_disability = False
    disab_reasons = []
    disab_fields = {
        "id_penglihatan": "Penglihatan",
        "id_pendengaran": "Pendengaran",
        "id_berjalan_atau_naik_tangga": "Mobilitas (Berjalan/Naik Tangga)",
        "id_menggunakan_tangan_jari": "Motorik (Tangan/Jari)",
        "id_belajar_kemampuan_intelektual": "Kognitif (Belajar/Intelektual)",
        "id_pengendalian_perilaku": "Perilaku",
        "id_berbicara_komunikasi": "Komunikasi",
        "id_mengurus_diri": "Perawatan Diri",
        "id_mengingat_berkonsentrasi": "Memori/Konsentrasi",
        "id_kesedihan_depresi": "Kesehatan Mental (Kesedihan/Depresi)"
    }
    for field, name in disab_fields.items():
        v = data.get(field)
        if v and "kesulitan" not in v.lower() and "tidak" not in v.lower() and "unknown" not in v.lower() and "ditanyakan" not in v.lower():
            # Hindari mendeteksi nilai numerik 4 atau 0 (Tidak ada kesulitan/default)
            v_clean = v.strip().lower()
            if v_clean in ("4", "0", "4.0", "0.0"):
                continue
            has_disability = True
            disab_reasons.append(f"Hambatan pada fungsi {name} ({v})")
            
    skor_aspd = data.get("skor_aspd", 0.0)
    if skor_aspd > 0.0:
        has_disability = True
        disab_reasons.append(f"Skor prioritas ASPD terhitung {skor_aspd}")

    # 2. Cek Kelayakan Kemiskinan (PKH Plus)
    is_poor = False
    pkh_reasons = []
    desil = data.get("desil_nasional", 10)
    if desil <= 4:
        is_poor = True
        pkh_reasons.append(f"Terdaftar dalam Desil Nasional {desil} (Kategori Miskin/Rentan)")
    skor_pkh = data.get("skor_pkh_plus", 0.0)
    if skor_pkh >= 50.0:
        is_poor = True
        pkh_reasons.append(f"Skor prioritas PKH Plus terhitung cukup tinggi ({skor_pkh})")

    # --- ATURAN SELEKSI KETAT & SALING SILANG (MUTUAL EXCLUSIVE USIA) ---
    # PKH Plus: lansia >= 70 tahun
    if is_poor and umur >= 70:
        status_pkh_str = "LAYAK"
        pkh_reasons.append(f"Usia lansia memenuhi syarat ({umur} tahun >= 70)")
    else:
        status_pkh_str = "TIDAK LAYAK"
        if is_poor and umur < 70:
            pkh_reasons.append(f"Usia lansia tidak memenuhi syarat ({umur} tahun < 70)")
        is_poor = False

    # ASPD: usia 6 bulan - 60 tahun (0.5 <= umur <= 60)
    if has_disability and (0.5 <= umur <= 60):
        status_aspd_str = "LAYAK"
        disab_reasons.append(f"Usia memenuhi rentang penerima ASPD ({umur} tahun berada di rentang 6 bulan - 60 tahun)")
    else:
        status_aspd_str = "TIDAK LAYAK"
        if has_disability and not (0.5 <= umur <= 60):
            disab_reasons.append(f"Usia tidak memenuhi rentang penerima ASPD ({umur} tahun tidak di rentang 6 bulan - 60 tahun)")
        has_disability = False

    justifikasi_pkh = " | ".join(pkh_reasons) if pkh_reasons else "Tidak memenuhi kriteria desil rendah untuk PKH Plus."
    justifikasi_aspd = " | ".join(disab_reasons) if disab_reasons else "Tidak terdeteksi hambatan disabilitas yang signifikan untuk ASPD."
    justifikasi_analisis = f"Analisis kelayakan untuk kepala keluarga {data.get('nama', 'Warga')}. Kelayakan PKH Plus: {status_pkh_str} ({justifikasi_pkh}). Kelayakan ASPD: {status_aspd_str} ({justifikasi_aspd})."

    # Bangun objek JSON respon laporan evaluasi
    content_obj = {
        "laporan_evaluasi": {
            "profil_warga": {
                "nik": data.get("nik", "Tidak diketahui"),
                "nama": data.get("nama", "Tidak diketahui"),
                "umur": f"{umur} tahun"
            },
            "analisis": {
                "justifikasi": justifikasi_analisis
            },
            "kesimpulan": {
                "pkh_plus": {
                    "status_kelayakan": status_pkh_str,
                    "urgensi": "TINGGI" if is_poor else "RENDAH",
                    "label": "Prioritas Penerima" if is_poor else "Tidak Prioritas",
                    "justifikasi": justifikasi_pkh
                },
                "aspd": {
                    "status_kelayakan": status_aspd_str,
                    "urgensi": "TINGGI" if has_disability else "RENDAH",
                    "label": "Rekomendasi Bantuan" if has_disability else "Tidak Direkomendasikan",
                    "justifikasi": justifikasi_aspd
                }
            }
        },
        "skor": {
            "skor_pkh_plus": skor_pkh,
            "skor_aspd": skor_aspd
        }
    }
    
    content_str = json.dumps(content_obj, ensure_ascii=False)
    
    # Kembalikan struktur respon standar OpenAI/RunPod
    return {
        "id": "chatcmpl-mock-dynamic",
        "object": "chat.completion",
        "created": 1717000000,
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_str
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 150,
            "total_tokens": 250
        }
    }


# HEALTH CHECK
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "Mock AI Server is running and Bedrock integrated..."}


if __name__ == "__main__":
    print("Menjalankan Server AI Jatim Sosial di Port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)