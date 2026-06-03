import os
import httpx
import logging
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app import models
from app.security import get_current_user
from app.config import AI_BASE_URL, AI_RUNPOD_URL, AI_RUNPOD_TOKEN
from app.schemas import item as item_schema

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/asesmen",
    tags=["4. Asesmen AI"]
)

# ==========================================
# FUNGSI SIMULASI RETRIEVER (QDRANT - TIM 3)
# ==========================================
async def mock_qdrant_retriever(query_text: str) -> str:
    """
    Simulasi pemanggilan database vektor Qdrant milik Tim 3.
    """
    return """
    [Konteks Kebijakan Sosial Jawa Timur]
    - PKH Plus: (a) lansia >= 70 tahun, (b) desil 1-4 DTSEN, (c) memiliki NIK Jawa Timur.
    - ASPD: (1) NIK Jawa Timur, (2) usia 6 bulan - 60 tahun, (3) penyandang disabilitas/bed ridden, (4) prioritas desil 1-5.
    """

def get_role_and_user_content(keluarga, skor_pkh, skor_aspd, konteks_aturan):
    """
    Fungsi bantuan untuk merakit prompt agar tidak ada kode yang diulang (DRY).
    """
    role_content = (
        "Anda adalah AI Auditor resmi Dinas Sosial Provinsi Jawa Timur yang bertugas melakukan verifikasi dan validasi kelayakan penerima manfaat dua program bantuan sosial:\n"
        "1. PKH Plus — Program Keluarga Harapan Plus, menyasar keluarga dengan kerentanan sosial-ekonomi berlapis (kemiskinan ekstrem, hunian tidak layak, masalah gizi, dan penyakit menahun).\n"
        "2. ASPD — Asistensi Sosial Penyandang Disabilitas, menyasar individu dengan hambatan fungsi fisik/mental signifikan yang mengurangi kemandirian dan kapasitas ekonomi.\n\n"
        "TUGAS ANDA:\n"
        "Untuk setiap profil warga, susun laporan evaluasi kelayakan yang sistematis dan dapat dipertanggungjawabkan secara administratif sesuai standar Kementerian Sosial RI.\n\n"
        "KERANGKA ANALISIS WAJIB (jalankan berurutan):\n"
        "1. PROFIL WARGA — Identifikasi identitas, posisi dalam keluarga, dan konteks sosial dasar.\n"
        "2. DEMOGRAFI — Nilai kelompok usia, status perkawinan, jumlah tanggungan, dan risiko sosial yang melekat.\n"
        "3. EKONOMI — Interpretasikan desil nasional: 1-2=miskin ekstrem, 3-4=rentan, 5-6=hampir miskin, 7-10=tidak miskin.\n"
        "4. INFRASTRUKTUR & HUNIAN — Nilai penguasaan bangunan dan luas lantai terhadap standar 36 m2 keluarga inti.\n"
        "5. KESEHATAN & GIZI — Evaluasi kondisi gizi dan penyakit menahun sebagai proxy beban ekonomi kesehatan.\n"
        "6. DISABILITAS & FUNGSI — Nilai 10 dimensi fungsi (penglihatan, pendengaran, mobilitas, tangan/jari, intelektual, perilaku, komunikasi, perawatan diri, memori/konsentrasi, kesedihan/depresi). Hambatan berat/total pada 1+ dimensi adalah indikator utama ASPD.\n"
        "7. SINTESIS — Agregasikan temuan, identifikasi co-occurring deprivation, dan berikan justifikasi LAYAK/TIDAK LAYAK untuk masing-masing program secara terpisah berdasarkan kriteria resmi berikut:\n"
        "   PKH Plus: (a) lansia >= 70 tahun, (b) desil 1-4 DTSEN, (c) memiliki NIK Jawa Timur.\n"
        "   ASPD: (1) NIK Jawa Timur, (2) usia 6 bulan - 60 tahun, (3) penyandang disabilitas/bed ridden, (4) prioritas desil 1-5; desil 6-10 wajib verifikasi lapangan.\n\n"
        "FORMAT OUTPUT:\n"
        "Seluruh respons WAJIB berupa satu objek JSON valid tanpa teks tambahan, tanpa markdown, tanpa komentar. Ikuti skema 'laporan_evaluasi' yang mencakup: profil_warga, analisis (per dimensi), skor, dan kesimpulan (untuk pkh_plus dan aspd masing-masing dengan status_kelayakan, urgensi, dan label)."
    )

    user_content = f"""Profil Warga:
- NIK              : {keluarga.nik or 'Tidak diketahui'}
- Nama             : {keluarga.nama_kepala_keluarga}
- Umur             : {getattr(keluarga, 'umur', 0)} tahun
- Hub. Kepala KK   : {getattr(keluarga, 'id_hubungan_kepala_keluarga', 'Kepala Keluarga')}
- Status Perkawinan: {getattr(keluarga, 'id_status_perkawinan', 'Tidak diketahui')}
- Desil Nasional   : {keluarga.desil_nasional}
- Jml. Anggota KK  : {keluarga.jumlah_anggota_keluarga} orang
- Penguasaan Bgn.  : {getattr(keluarga, 'id_status_kepemilikan_bangunan', 'Milik Sendiri')}
- Luas Bangunan    : {getattr(keluarga, 'luas_lantai', 0.0)} m2
- Kondisi Gizi     : Tidak diketahui
- Penyakit Menahun : Tidak diketahui
- Penglihatan      : {keluarga.id_penglihatan or 'Tidak mengalami kesulitan'}
- Pendengaran      : {getattr(keluarga, 'id_pendengaran', 'Tidak mengalami kesulitan')}
- Berjalan/Tangga  : {keluarga.id_berjalan_atau_naik_tangga or 'Tidak mengalami kesulitan'}
- Tangan/Jari      : {getattr(keluarga, 'id_penggunaan_tangan_dan_jari', 'Tidak mengalami kesulitan')}
- Belajar/Intelektual: {getattr(keluarga, 'id_belajar_atau_intelektual', 'Tidak mengalami kesulitan')}
- Pengendalian Perilaku: {getattr(keluarga, 'id_perilaku', 'Tidak mengalami kesulitan')}
- Bicara/Komunikasi: {getattr(keluarga, 'id_berbicara_atau_komunikasi', 'Tidak mengalami kesulitan')}
- Mengurus Diri    : {getattr(keluarga, 'id_mengurus_diri_sendiri', 'Tidak mengalami kesulitan')}
- Memori/Konsentrasi: {getattr(keluarga, 'id_mengingat_atau_konsentrasi', 'Tidak mengalami kesulitan')}
- Kesedihan/Depresi: {getattr(keluarga, 'id_sedih_atau_depresi', 'Tidak mengalami kesulitan')}
- Status DTSEN     : DTSEN AKTIF
- Wilayah          : Jawa Timur
- Izin Usaha       : Tidak diketahui
- Jml. Jenis Usaha : 0
- Omset Usaha Utama: Tidak diketahui

Skor Prioritas Bantuan (semakin mendekati 100 = semakin prioritas):
- Skor PKH Plus    : {skor_pkh}
- Skor ASPD        : {skor_aspd}

Tolong buatkan laporan evaluasi kelayakan untuk program PKH Plus dan ASPD.
Kamu harus merujuk pada aturan berikut sebagai konteks kebijakan:
<hasil_retrieval>
{konteks_aturan}
</hasil_retrieval>
"""
    return role_content, user_content


def extract_rekomendasi(hasil_final: dict) -> list:
    """Fungsi aman untuk mengekstrak array rekomendasi bantuan dari format JSON Tim 3"""
    rekomendasi = []
    try:
        kesimpulan = hasil_final.get("laporan_evaluasi", {}).get("kesimpulan", {})
        
        # Cek PKH Plus (Pastikan tulisannya LAYAK dan bukan TIDAK LAYAK)
        status_pkh = str(kesimpulan.get("pkh_plus", {}).get("status_kelayakan", "")).upper().strip()
        if status_pkh == "LAYAK":
            rekomendasi.append("PKH Plus")
            
        # Cek ASPD
        status_aspd = str(kesimpulan.get("aspd", {}).get("status_kelayakan", "")).upper().strip()
        if status_aspd == "LAYAK":
            rekomendasi.append("ASPD")
            
    except Exception as e:
        logger.error(f"Gagal mengekstrak rekomendasi dari JSON AI: {e}")
    
    return rekomendasi

# ==========================================
# FUNGSI BACKGROUND (ASINKRON) UNTUK AI
# ==========================================

async def execute_asesmen_sosial_logic_async(keluarga_id: UUID, user_id: UUID, db: Session):
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.id == keluarga_id).first()
    if not keluarga:
        print(f"[Asinkron] Keluarga {keluarga_id} tidak ditemukan.")
        return
    
    hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()
    skor_pkh = hitung.skor_pkh_plus if hitung and hitung.skor_pkh_plus else 0.0
    skor_aspd = hitung.skor_aspd if hitung and hitung.skor_aspd else 0.0

    try:
        konteks_aturan = await mock_qdrant_retriever("syarat penerima bansos")
        role_content, user_content = get_role_and_user_content(keluarga, skor_pkh, skor_aspd, konteks_aturan)

        # Payload Model Baru (Runpod/OpenAI)
        payload_llm = {
            "model": "aitf-ub-2026/cpt-qwen3-8b-sft_v1",
            "messages": [
                {"role": "system", "content": role_content},
                {"role": "user", "content": user_content}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        headers_runpod = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AI_RUNPOD_TOKEN}"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    AI_RUNPOD_URL,
                    headers=headers_runpod,
                    json=payload_llm,
                    timeout=60.0 # Waktu tunggu dinaikkan ke 60s
                )
                response.raise_for_status()
                hasil_mentah = response.json()
                
                # Mengubah balasan string JSON Runpod menjadi Dictionary
                string_json_ai = hasil_mentah["choices"][0]["message"]["content"]
                hasil_final = json.loads(string_json_ai)
            except Exception as e:
                print(f"[Asinkron AI Error] Gagal memanggil Runpod: {e}")
                return

        rekomendasi_baru = extract_rekomendasi(hasil_final)
        analisis_rag = json.dumps(hasil_final) 

        bantuan_lama = None

        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=user_id)
            db.add(hitung)
        else:
            bantuan_lama = hitung.rekomendasi_bantuan

        hitung.rekomendasi_bantuan = rekomendasi_baru
        hitung.reasoning_tim3 = analisis_rag
        hitung.status_validasi = "analisis"

        log = models.LogHistori(
            keluarga_id=keluarga.id,
            user_id=user_id,
            desil_lama=None,
            desil_baru=None,
            bantuan_lama=bantuan_lama,
            bantuan_baru=rekomendasi_baru
        )
        db.add(log)
        db.commit()
        print(f"[Asinkron] Asesmen sukses untuk KK {keluarga.no_kk}. Rekomendasi: {rekomendasi_baru}")
    except Exception as e:
        db.rollback()
        print(f"[Asinkron DB Error] {e}")


def run_async_assessment(keluarga_id: UUID, user_id: UUID):
    db_gen = get_db()
    db = next(db_gen)
    try:
        asyncio.run(execute_asesmen_sosial_logic_async(keluarga_id, user_id, db))
    finally:
        db.close()


# ==========================================
# FUNGSI VALIDASI VISUAL TIM 2 
# ==========================================
async def perform_visual_validation(keluarga_id: UUID, user_id: UUID, db: Session):
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.id == keluarga_id).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")

    foto_tampak_luar = db.query(models.Foto).filter(
        models.Foto.keluarga_id == keluarga_id,
        models.Foto.tampak_dalam == False
    ).order_by(models.Foto.diunggah_pada.desc()).first()

    foto_tampak_dalam = db.query(models.Foto).filter(
        models.Foto.keluarga_id == keluarga_id,
        models.Foto.tampak_dalam == True
    ).order_by(models.Foto.diunggah_pada.desc()).first()

    foto_utama = foto_tampak_luar if foto_tampak_luar else db.query(models.Foto).filter(
        models.Foto.keluarga_id == keluarga_id
    ).order_by(models.Foto.diunggah_pada.desc()).first()

    if not foto_utama:
        raise HTTPException(status_code=400, detail="Foto rumah tidak ditemukan untuk keluarga ini.")

    url_foto_luar = foto_tampak_luar.url_foto if foto_tampak_luar else foto_utama.url_foto
    url_foto_dalam = foto_tampak_dalam.url_foto if foto_tampak_dalam else None

    payload_ke_tim2 = {
        "image_url": url_foto_luar,
        "foto_rumah_tampak_dalam": url_foto_dalam,
        "konteks_rumah": {
            "jenis_lantai_terluas": keluarga.id_lantai_terluas,
            "jenis_dinding_terluas": keluarga.id_dinding_terluas,
            "jenis_atap_terluas": keluarga.id_atap_terluas,
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            res_ai = await client.post(
                f"{AI_BASE_URL}/api/ai/visual-validator",
                json=payload_ke_tim2,
                timeout=30.0
            )
            res_ai.raise_for_status()
            hasil_validator = res_ai.json()

        is_match = hasil_validator.get("is_match", True)
        reasoning = hasil_validator.get("reasoning", "Validasi visual selesai.")

        hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()

        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=user_id)
            db.add(hitung)

        hitung.ada_ketidaksesuaian_visual = not is_match
        hitung.reasoning_tim2 = reasoning
        hitung.foto_id_digunakan = foto_utama.id

        db.commit()

        return {
            "status": "Sukses",
            "validation": {
                "is_match": is_match,
                "reasoning": reasoning
            },
            "url_foto_divalidasi": foto_utama.url_foto,
            "hasil_tim2": hasil_validator
        }
    except Exception as e:
        logger.error("Gagal terhubung ke server Tim 2.", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Kesalahan koneksi ke Tim 2: {str(e)}")


async def run_async_visual_validation(keluarga_id: UUID, user_id: UUID):
    db_gen = get_db()
    db = next(db_gen)
    try:
        await perform_visual_validation(keluarga_id, user_id, db)
        print(f"[Asinkron] Validasi visual sukses untuk KK {keluarga_id}")
    except Exception as e:
        db.rollback()
        print(f"[Asinkron Visual Error] {e}")
    finally:
        db.close()


# ==========================================
# ENDPOINT ASESMEN (TRIGGER MANUAL)
# ==========================================

@router.post("/sosial", summary="Analisis Tim 1 yang diteruskan ke Tim 3")
async def asesmen_sosial(
    payload: item_schema.TriggerAsesmenRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keluarga = db.query(models.Keluarga).filter(
        models.Keluarga.id == payload.keluarga_id
    ).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")

    hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()
    skor_pkh = hitung.skor_pkh_plus if hitung and hitung.skor_pkh_plus else 0.0
    skor_aspd = hitung.skor_aspd if hitung and hitung.skor_aspd else 0.0

    try:
        konteks_aturan = await mock_qdrant_retriever("syarat penerima bansos")
        role_content, user_content = get_role_and_user_content(keluarga, skor_pkh, skor_aspd, konteks_aturan)

        payload_llm = {
            "model": "aitf-ub-2026/cpt-qwen3-8b-sft_v1",
            "messages": [
                {"role": "system", "content": role_content},
                {"role": "user", "content": user_content}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        headers_runpod = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AI_RUNPOD_TOKEN}"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    AI_RUNPOD_URL,
                    headers=headers_runpod,
                    json=payload_llm,
                    timeout=60.0
                )
                response.raise_for_status()
                hasil_mentah = response.json()
                
                # Parsing string JSON dari Runpod
                string_json_ai = hasil_mentah["choices"][0]["message"]["content"]
                hasil_final = json.loads(string_json_ai)
                
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Gagal mendapatkan analisis dari Runpod: {e}")

        rekomendasi_baru = extract_rekomendasi(hasil_final)
        analisis_rag = json.dumps(hasil_final) 

        bantuan_lama = None

        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=current_user.id)
            db.add(hitung)
        else:
            bantuan_lama = hitung.rekomendasi_bantuan

        hitung.rekomendasi_bantuan = rekomendasi_baru
        hitung.reasoning_tim3 = analisis_rag

        log = models.LogHistori(
            keluarga_id=keluarga.id, user_id=current_user.id,
            desil_lama=None, desil_baru=None,
            bantuan_lama=bantuan_lama, bantuan_baru=rekomendasi_baru
        )
        db.add(log)
        db.commit()

        return {
            "status": "Sukses",
            "nomor_kk": keluarga.no_kk,
            "hasil_rekomendasi_final": rekomendasi_baru,
            "justifikasi_dokumen": json.loads(analisis_rag) # Diubah kembali ke JSON dict untuk respon API
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Kesalahan internal: {str(e)}")

# ASESMEN VISUAL — TIM 2
@router.post("/visual/{id_keluarga}", summary="Trigger AI Visual mengirim URL dan ID ke Tim 2")
async def asesmen_visual(
    id_keluarga: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.id == id_keluarga).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")

    foto_tampak_luar = db.query(models.Foto).filter(
        models.Foto.keluarga_id == id_keluarga,
        models.Foto.tampak_dalam == False
    ).order_by(models.Foto.diunggah_pada.desc()).first()

    foto_tampak_dalam = db.query(models.Foto).filter(
        models.Foto.keluarga_id == id_keluarga,
        models.Foto.tampak_dalam == True
    ).order_by(models.Foto.diunggah_pada.desc()).first()

    foto_utama = foto_tampak_luar or foto_tampak_dalam
    if not foto_utama:
        raise HTTPException(status_code=400, detail="Foto rumah tidak ditemukan untuk keluarga ini.")

    url_foto_luar = foto_tampak_luar.url_foto if foto_tampak_luar else foto_utama.url_foto
    url_foto_dalam = foto_tampak_dalam.url_foto if foto_tampak_dalam else None

    payload_ke_tim2 = {
        "id_data": str(keluarga.id),
        "foto_rumah": url_foto_luar,
        "foto_rumah_tampak_dalam": url_foto_dalam,
        "id_atap_terluas": keluarga.id_atap_terluas,
        "id_dinding_terluas": keluarga.id_dinding_terluas,
        "id_lantai_terluas": keluarga.id_lantai_terluas
    }

    try:
        async with httpx.AsyncClient() as client:
            res_ai = await client.post(
                f"{AI_BASE_URL}/api/ai/visual-validator",
                json=payload_ke_tim2,
                timeout=30.0
            )
            res_ai.raise_for_status() 
            hasil_validator = res_ai.json() 

        hitung = db.query(models.Perhitungan).filter(
            models.Perhitungan.keluarga_id == keluarga.id
        ).first()
        
        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=current_user.id)
            db.add(hitung)

        is_match = hasil_validator.get("is_match", True)
        reasoning = hasil_validator.get("reasoning", str(hasil_validator))

        hitung.ada_ketidaksesuaian_visual = not is_match
        hitung.reasoning_tim2 = reasoning
        hitung.foto_id_digunakan = foto_utama.id

        db.commit()

        return {
            "status": "Sukses",
            "url_foto_dikirim": {
                "luar": url_foto_luar,
                "dalam": url_foto_dalam
            },
            "hasil_tim2": hasil_validator
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Kesalahan koneksi ke Tim 2: {str(e)}")

# ==========================================
# ENDPOINT MASTER (1 TOMBOL UNTUK SEMUA)
# ==========================================

@router.post("/komprehensif/{id_keluarga}", summary="Jalankan Semua Analisis (Tim 1, 2, & 3) Sekaligus")
async def asesmen_komprehensif_semua_tim(
    id_keluarga: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint ini digunakan oleh Frontend jika hanya ada 1 tombol 'Analisis'.
    Akan mengeksekusi Tim 1, Tim 2, dan Tim 3 secara berurutan/paralel dan merangkum hasilnya.
    """
    # Karena asesmen_sosial butuh payload khusus, kita buat mock payload-nya
    payload_sosial = item_schema.TriggerAsesmenRequest(keluarga_id=id_keluarga)

    hasil_sosial = None
    hasil_visual = None
    error_messages = []

    # 1. JALANKAN TIM 1 & 3 (Sosial & RAG)
    try:
        hasil_sosial = await asesmen_sosial(payload=payload_sosial, current_user=current_user, db=db)
    except Exception as e:
        logger.error(f"Error Tim 1 & 3: {e}")
        error_messages.append(f"Gagal memproses analisis sosial: {str(e)}")

    # 2. JALANKAN TIM 2 (Visual)
    try:
        hasil_visual = await asesmen_visual(id_keluarga=id_keluarga, current_user=current_user, db=db)
    except Exception as e:
        logger.error(f"Error Tim 2: {e}")
        error_messages.append(f"Gagal memproses validasi visual: {str(e)}")

    # 3. GABUNGKAN HASILNYA KE FRONTEND
    return {
        "status": "Selesai",
        "pesan": "Proses asesmen komprehensif selesai dieksekusi.",
        "error": error_messages if error_messages else None,
        "hasil_analisis_sosial_tim3": hasil_sosial,
        "hasil_validasi_visual_tim2": hasil_visual
    }