import os
import httpx
import logging
import json
import asyncio
import base64
from app.utils import enum
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app import models
from app.security import get_current_user
from app.config import AI_BASE_URL, AI_RUNPOD_URL, AI_RUNPOD_TOKEN, API_TIM_3_URL
from app.schemas import item as item_schema

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/asesmen",
    tags=["4. Asesmen AI"]
)

# =====================================================================
# BAGIAN 1: FUNGSI BANTUAN (HELPERS)
# =====================================================================

def get_role_and_user_content(keluarga, skor_pkh, skor_aspd):
    role_content = """Anda adalah AI Auditor resmi Dinas Sosial Provinsi Jawa Timur yang bertugas melakukan verifikasi dan validasi kelayakan penerima manfaat dua program bantuan sosial.

TUGAS ANDA:
Berdasarkan PROFIL WARGA dan KONTEKS PROGRAM BANTUAN yang disediakan, evaluasi kelayakan warga HANYA untuk 2 program utama berikut:
1. Asistensi Sosial Penyandang Disabilitas (ASPD)
2. PKH Plus (Lanjut Usia 70+)

=== INSTRUKSI PENTING ===
1. Evaluasi hanya 2 program utama di atas secara individual.
2. Tentukan status: "ELIGIBLE" atau "TIDAK_ELIGIBLE".
3. Ranking dari yang paling cocok ke yang paling tidak cocok.
4. Berikan reasoning yang jelas dan WAJIB mengutip sumber dokumen resmi juknis.
5. JANGAN merekomendasikan program bantuan di luar 2 program utama tersebut.
6. DILARANG KERAS menyebut Program Sembako, PKH reguler, BPNT, PBI Jaminan Kesehatan, Rutilahu, PIP, Jamkesda, atau bantuan tambahan lainnya.

=== FORMAT OUTPUT (STRICT JSON) ===
Anda WAJIB merespons HANYA dengan objek JSON valid tanpa tag markdown (seperti ```json), tanpa komentar, dan tanpa teks pembuka/penutup. 
Gunakan skema dan urutan persis seperti di bawah ini:
{
  "ringkasan_profil": "<string konkret berisi umur, desil, dll>",
  "rekomendasi": [{"rank": 1, "nama_program": "...", "status": "ELIGIBLE", "dasar_hukum": "...", "alasan_kelayakan": "..."}],
  "rekomendasi_teknis_bansos": "<string narasi tunggal atau null>",
  "program_tidak_sesuai": [{"nama_program": "...", "status": "TIDAK_ELIGIBLE", "alasan": "..."}]
}

PERINGATAN TERAKHIR: Jangan mengosongkan alasan. Keluarkan HANYA output JSON.
"""    
    user_content = f"""PROFIL WARGA
- NIK / No. KK     : {getattr(keluarga, 'nik', 'Tidak diketahui')} / {getattr(keluarga, 'no_kk', 'Tidak diketahui')}
- Nama             : {getattr(keluarga, 'nama', 'Tidak diketahui')}
- Umur             : {getattr(keluarga, 'umur_2026', 'Tidak diketahui')} tahun
- Hub. Kepala KK   : {enum.HubKepalaEnum.label(getattr(keluarga, 'id_hub_kepala_keluarga', 'Tidak diketahui'))}
- Status Kawin     : {enum.StatusPerkawinanEnum.label(getattr(keluarga, 'id_status_perkawinan', 'Tidak diketahui'))}
- Jml. Anggota KK  : {getattr(keluarga, 'jumlah_anggota_keluarga', 'Tidak diketahui')} orang
- Desil Nasional   : {getattr(keluarga, 'desil_nasional_keluarga', 'Tidak diketahui')} | Status DTSEN: {getattr(keluarga, 'status_dtsen', 'Tidak diketahui')}
- Status Keberadaan: {enum.StatusKeberadaanEnum.label(getattr(keluarga, 'id_status_keberadaan_keluarga', 'Tidak diketahui'))}
- Bansos           : {getattr(keluarga, 'bansos', 'Tidak diketahui')}
- PBI Jaminan Kes  : {getattr(keluarga, 'pbi', 'Tidak diketahui')}
- Kondisi Gizi     : {enum.KondisiGiziEnum.label(getattr(keluarga, 'id_kondisi_gizi', 'Tidak diketahui'))}
- Penyakit Menahun : {enum.PenyakitMenahunEnum.label(getattr(keluarga, 'id_penyakit_menahun', 'Tidak diketahui'))}
Hambatan Fungsi:
- Penglihatan      : {enum.HambatanFungsiEnum.label(getattr(keluarga, 'id_penglihatan', 'Tidak diketahui'))} | Pendengaran: {enum.HambatanFungsiEnum.label(getattr(keluarga, 'id_pendengaran', 'Tidak diketahui'))}
- Berjalan/Tangga  : {enum.HambatanFungsiEnum.label(getattr(keluarga, 'id_berjalan_atau_naik_tangga', 'Tidak diketahui'))} | Tangan/Jari: {enum.HambatanFungsiEnum.label(getattr(keluarga, 'id_menggunakan_tangan_jari', 'Tidak diketahui'))}
- Belajar/Intelek  : {enum.HambatanFungsiEnum.label(getattr(keluarga, 'id_belajar_kemampuan_intelektual', 'Tidak diketahui'))} | Perilaku: {enum.HambatanFungsiEnum.label(getattr(keluarga, 'id_pengendalian_perilaku', 'Tidak diketahui'))}
- Bicara/Komunikasi: {enum.HambatanFungsiEnum.label(getattr(keluarga, 'id_berbicara_komunikasi', 'Tidak diketahui'))} | Mengurus Diri: {enum.HambatanFungsiEnum.label(getattr(keluarga, 'id_mengurus_diri', 'Tidak diketahui'))}
- Ingatan/Fokus    : {enum.HambatanFungsiEnum.label(getattr(keluarga, 'id_mengingat_berkonsentrasi', 'Tidak diketahui'))} | Sedih/Depresi: {enum.HambatanFungsiEnum.label(getattr(keluarga, 'id_kesedihan_depresi', 'Tidak diketahui'))}
- Wilayah          : Provinsi {getattr(keluarga, 'kode_provinsi', 'Tidak diketahui')}

Tolong buatkan laporan evaluasi kelayakan untuk program PKH Plus dan ASPD.
"""
    return role_content, user_content


def extract_rekomendasi(hasil_final: dict) -> list:
    rekomendasi = []
    try:
        rekomendasi_list = hasil_final.get("rekomendasi", [])
        for rek in rekomendasi_list:
            if rek.get("status") == "ELIGIBLE":
                rekomendasi.append(rek.get("nama_program"))
    except Exception as e:
        logger.error(f"Gagal mengekstrak rekomendasi dari JSON AI: {e}")
    return rekomendasi


async def fetch_image_as_base64(url: str) -> str:
    if not url: return None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            base64_encoded = base64.b64encode(response.content).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_encoded}"
    except Exception as e:
        logger.error(f"Gagal mengunduh gambar {url}: {e}")
        return None

# =====================================================================
# BAGIAN 2: SERVICE LAYER (MESIN UTAMA LOGIKA AI)
# =====================================================================

async def perform_social_assessment(keluarga_id: UUID, user_id: UUID, db: Session):
    """Mesin utama untuk Asesmen Sosial (Tim 1 & 3)"""
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.id == keluarga_id).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")

    hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()
    skor_pkh = hitung.skor_pkh_plus if hitung and hitung.skor_pkh_plus else 0.0
    skor_aspd = hitung.skor_aspd if hitung and hitung.skor_aspd else 0.0

    role_content, user_content = get_role_and_user_content(keluarga, skor_pkh, skor_aspd)

    payload_llm = {
        "model": "aitf-ub-2026/cpt-qwen3-8b-sft_v1",
        "messages": [
            {"role": "system", "content": role_content},
            {"role": "user", "content": user_content}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2, # Lebih kecil agar tidak halusinasi
        "max_tokens": 1024,
        "keluarga_id": str(keluarga.id)
    }
    
    headers_runpod = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_RUNPOD_TOKEN}"
    }

    try:
        async with httpx.AsyncClient() as client:
            # Gunakan URL yang konsisten. Sesuaikan dengan config-mu
            url_target = AI_RUNPOD_URL if AI_RUNPOD_URL else f"{API_TIM_3_URL}/recommend"
            response = await client.post(url_target, headers=headers_runpod, json=payload_llm, timeout=60.0)
            response.raise_for_status()
            hasil_mentah = response.json()
            
            if "choices" in hasil_mentah:
                string_json_ai = hasil_mentah["choices"][0]["message"]["content"]
                hasil_final = json.loads(string_json_ai)
            else:
                hasil_final = hasil_mentah.get("justifikasi_dokumen", hasil_mentah)
                
    except Exception as e:
        logger.error(f"Gagal memanggil AI Sosial: {e}")
        raise HTTPException(status_code=502, detail=f"Gagal mendapatkan analisis dari LLM: {e}")

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
        keluarga_id=keluarga.id, user_id=user_id,
        bantuan_lama=bantuan_lama, bantuan_baru=rekomendasi_baru
    )
    db.add(log)
    db.commit()

    return {
        "status": "Sukses",
        "nomor_kk": keluarga.no_kk,
        "hasil_rekomendasi_final": rekomendasi_baru,
        "skor_pkh": skor_pkh,
        "skor_aspd": skor_aspd,
        "justifikasi_dokumen": hasil_final
    }


async def perform_visual_validation(keluarga_id: UUID, user_id: UUID, db: Session):
    """Mesin utama untuk Asesmen Visual (Tim 2)"""
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.id == keluarga_id).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Keluarga tidak ditemukan")

    foto_tampak_luar = db.query(models.Foto).filter(models.Foto.keluarga_id == keluarga_id, models.Foto.tampak_dalam == False).order_by(models.Foto.diunggah_pada.desc()).first()
    foto_tampak_dalam = db.query(models.Foto).filter(models.Foto.keluarga_id == keluarga_id, models.Foto.tampak_dalam == True).order_by(models.Foto.diunggah_pada.desc()).first()

    url_luar = foto_tampak_luar.url_foto if foto_tampak_luar else None
    url_dalam = foto_tampak_dalam.url_foto if foto_tampak_dalam else None

    base64_luar = await fetch_image_as_base64(url_luar)
    base64_dalam = await fetch_image_as_base64(url_dalam)

    system_prompt_global = """Anda adalah Ahli Pemeriksa Fisik Bangunan dari Dinas Sosial. 
Tugas Anda memvalidasi kesesuaian material fisik bangunan dengan data profil warga.
Jawab WAJIB menggunakan JSON dengan key 'is_match' (boolean) dan 'reasoning' (string)."""

    teks_konteks_rumah = (
        f"\n\n[DATA PROFIL UNTUK DIVALIDASI]\n"
        f"- ID Lantai Terluas: {keluarga.id_lantai_terluas}\n"
        f"- ID Dinding Terluas: {keluarga.id_dinding_terluas}\n"
        f"- ID Atap Terluas: {keluarga.id_atap_terluas}\n"
        "Cocokkan kondisi di foto dengan data profil di atas."
    )

    user_prompt_terpilih = ""
    gambar_dikirim = []

    if base64_luar and base64_dalam:
        user_prompt_terpilih = "Ini adalah foto tampak luar dan dalam rumah warga. Silakan evaluasi ketiganya." + teks_konteks_rumah
        gambar_dikirim = [{"type": "image_url", "image_url": {"url": base64_luar}}, {"type": "image_url", "image_url": {"url": base64_dalam}}]
    elif base64_luar and not base64_dalam:
        user_prompt_terpilih = "Ini HANYA foto tampak luar. Tolong evaluasi atap dan dindingnya saja." + teks_konteks_rumah
        gambar_dikirim = [{"type": "image_url", "image_url": {"url": base64_luar}}]
    elif not base64_luar and base64_dalam:
        user_prompt_terpilih = "Ini HANYA foto tampak dalam. Tolong evaluasi lantai dan dinding dalamnya saja." + teks_konteks_rumah
        gambar_dikirim = [{"type": "image_url", "image_url": {"url": base64_dalam}}]
    else:
        raise HTTPException(status_code=400, detail="Tidak ada foto untuk dianalisis.")

    payload_ke_tim2 = {
        "model": "model-vision-tim-2", 
        "messages": [
            {"role": "system", "content": system_prompt_global},
            {"role": "user", "content": [{"type": "text", "text": user_prompt_terpilih}, *gambar_dikirim]}
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 500
    }

    try:
        async with httpx.AsyncClient() as client:
            res_ai = await client.post(f"{AI_BASE_URL}/api/ai/visual-validator", json=payload_ke_tim2, timeout=60.0)
            res_ai.raise_for_status()
            hasil_validator = res_ai.json()
            
            if "choices" in hasil_validator:
                hasil_ekstrak = json.loads(hasil_validator["choices"][0]["message"]["content"])
                is_match = hasil_ekstrak.get("is_match", True)
                reasoning = hasil_ekstrak.get("reasoning", "Validasi visual selesai.")
            else:
                is_match = hasil_validator.get("is_match", True)
                reasoning = hasil_validator.get("reasoning", "Validasi visual selesai.")

    except Exception as e:
        logger.error("Gagal terhubung ke server Tim 2.", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Kesalahan koneksi ke Tim 2: {str(e)}")

    hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()
    if not hitung:
        hitung = models.Perhitungan(keluarga_id=keluarga_id, user_id=user_id)
        db.add(hitung)

    hitung.ada_ketidaksesuaian_visual = not is_match
    hitung.reasoning_tim2 = reasoning
    hitung.foto_id_digunakan = foto_tampak_luar.id if foto_tampak_luar else (foto_tampak_dalam.id if foto_tampak_dalam else None)

    db.commit()

    return {
        "status": "Sukses",
        "validation": {"is_match": is_match, "reasoning": reasoning},
        "url_foto_divalidasi": [url_luar, url_dalam],
        "hasil_tim2": hasil_validator
    }


# =====================================================================
# BAGIAN 3: ENDPOINTS / ROUTES (TOMBOL UI)
# =====================================================================

@router.post("/sosial", summary="Analisis Tim 1 yang diteruskan ke Tim 3")
async def asesmen_sosial(
    payload: item_schema.TriggerAsesmenRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint manual khusus untuk Asesmen Sosial"""
    return await perform_social_assessment(payload.keluarga_id, current_user.id, db)


@router.post("/visual-validator", summary="Validasi Fisik Rumah Dinamis ke Tim 2")
async def asesmen_visual(
    keluarga_id: UUID, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint manual khusus untuk Validasi Visual"""
    return await perform_visual_validation(keluarga_id, current_user.id, db)


@router.post("/komprehensif/{id_keluarga}", summary="Jalankan Semua Analisis (Tim 1, 2, & 3) Sekaligus")
async def asesmen_komprehensif_semua_tim(
    id_keluarga: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint jika Frontend hanya memiliki 1 tombol 'Analisis Semua'."""
    hasil_sosial = None
    hasil_visual = None
    error_messages = []

    try:
        hasil_sosial = await perform_social_assessment(id_keluarga, current_user.id, db)
    except Exception as e:
        logger.error(f"Error Tim 1 & 3: {e}")
        error_messages.append(f"Gagal memproses analisis sosial: {str(e)}")

    try:
        hasil_visual = await perform_visual_validation(id_keluarga, current_user.id, db)
    except Exception as e:
        logger.error(f"Error Tim 2: {e}")
        error_messages.append(f"Gagal memproses validasi visual: {str(e)}")

    return {
        "status": "Selesai",
        "pesan": "Proses asesmen komprehensif selesai dieksekusi.",
        "error": error_messages if error_messages else None,
        "hasil_analisis_sosial_tim3": hasil_sosial,
        "hasil_validasi_visual_tim2": hasil_visual
    }

# =====================================================================
# BAGIAN 4: BACKGROUND TASKS (JIKA DIBUTUHKAN)
# =====================================================================

def run_async_assessment(keluarga_id: UUID, user_id: UUID):
    db_gen = get_db()
    db = next(db_gen)
    try:
        asyncio.run(perform_social_assessment(keluarga_id, user_id, db))
    finally:
        db.close()

def run_async_visual_validation(keluarga_id: UUID, user_id: UUID):
    db_gen = get_db()
    db = next(db_gen)
    try:
        asyncio.run(perform_visual_validation(keluarga_id, user_id, db))
    finally:
        db.close()