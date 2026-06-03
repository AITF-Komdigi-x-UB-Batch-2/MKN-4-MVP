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
from app.config import AI_BASE_URL
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
        # 1. Tarik Konteks Qdrant
        konteks_aturan = await mock_qdrant_retriever("syarat penerima bansos")

        # 2. Rakit Prompt (Role & User Content)
        role_content = (
            "Anda adalah AI Auditor resmi Dinas Sosial Provinsi Jawa Timur yang bertugas "
            "melakukan verifikasi kelayakan penerima manfaat PKH Plus dan ASPD. "
            "Balas HANYA dengan JSON valid berisi: status_kelayakan, urgensi, rekomendasi_bantuan (array), dan reasoning."
        )

        user_content = f"""
        Profil Warga:
        - NIK: {keluarga.nik or 'Tidak diketahui'}
        - Nama: {keluarga.nama_kepala_keluarga}
        - Desil Nasional: {keluarga.desil_nasional}
        - Penglihatan: {keluarga.id_penglihatan}
        - Mobilitas: {keluarga.id_berjalan_atau_naik_tangga}

        Skor Prioritas:
        - Skor PKH Plus: {skor_pkh}
        - Skor ASPD: {skor_aspd}

        Evaluasi kelayakan berdasarkan kebijakan berikut:
        <hasil_retrieval>
        {konteks_aturan}
        </hasil_retrieval>
        """

        # Ini adalah payload yang akan dikirim ke Beeceptor / AI Tim 3
        payload_llm = {
            "messages": [
                {"role": "system", "content": role_content},
                {"role": "user", "content": user_content}
            ],
            "desil": keluarga.desil_nasional, 
            "skor_aspd": skor_aspd,           
            "skor_pkh": skor_pkh              # <--- Sudah ditambahkan di sini
        }

        # 3. Eksekusi ke URL AI (Beeceptor / Tim 3)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{AI_BASE_URL}/api/chat", # <-- Memanggil URL di .env
                    json=payload_llm,
                    timeout=30.0
                )
                response.raise_for_status()
                hasil_final = response.json()
            except Exception as e:
                print(f"[Asinkron AI Error] Gagal mendapatkan analisis: {e}")
                return

        rekomendasi_baru = hasil_final.get("rekomendasi_bantuan", [])
        analisis_rag = json.dumps(hasil_final) # Simpan semua response sebagai reasoning

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
        print(f"[Asinkron] Asesmen sukses untuk KK {keluarga.no_kk}")
    except Exception as e:
        db.rollback()
        print(f"[Asinkron DB Error] {e}")

# Fungsi wrapper untuk BackgroundTasks
def run_async_assessment(keluarga_id: UUID, user_id: UUID):
    db_gen = get_db()
    db = next(db_gen)
    try:
        # Panggil versi async di dalam thread sinkron
        asyncio.run(execute_asesmen_sosial_logic_async(keluarga_id, user_id, db))
    finally:
        db.close()


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

        role_content = "Anda adalah AI Auditor resmi Dinas Sosial Provinsi Jawa Timur..."
        user_content = f"Profil Warga:\n- NIK: {keluarga.nik}\n- Desil: {keluarga.desil_nasional}\n- Skor PKH: {skor_pkh}\n- Skor ASPD: {skor_aspd}\n\nKonteks: {konteks_aturan}"

        # Payload manual untuk Swagger
        payload_llm = {
            "messages": [
                {"role": "system", "content": role_content},
                {"role": "user", "content": user_content}
            ],
            "desil": keluarga.desil_nasional, 
            "skor_aspd": skor_aspd,
            "skor_pkh": skor_pkh              # <--- Sudah ditambahkan di sini juga
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{AI_BASE_URL}/api/chat", # <-- Memanggil Beeceptor
                    json=payload_llm,
                    timeout=30.0
                )
                response.raise_for_status()
                hasil_final = response.json()
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Gagal mendapatkan analisis dari AI LLM: {e}")

        rekomendasi_baru = hasil_final.get("rekomendasi_bantuan", [])
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
            "justifikasi_dokumen": analisis_rag
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
    # 1. Cek Data Keluarga & Foto
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

    # 2. Siapkan Payload JSON sesuai permintaan Tim 2
    payload_ke_tim2 = {
        "id_data": str(keluarga.id),
        "foto_rumah": url_foto_luar,
        "foto_rumah_tampak_dalam": url_foto_dalam,
        "id_atap_terluas": keluarga.id_atap_terluas,
        "id_dinding_terluas": keluarga.id_dinding_terluas,
        "id_lantai_terluas": keluarga.id_lantai_terluas
    }

    try:
        # 3. Tembak Endpoint Tim 2
        async with httpx.AsyncClient() as client:
            res_ai = await client.post(
                f"{AI_BASE_URL}/api/ai/visual-validator",
                json=payload_ke_tim2,
                timeout=30.0
            )
            res_ai.raise_for_status() 
            hasil_validator = res_ai.json() 

        # 4. Tangkap Response Bersarang (Nested JSON) dari Tim 2 & SIMPAN KE DB
        hitung = db.query(models.Perhitungan).filter(
            models.Perhitungan.keluarga_id == keluarga.id
        ).first()
        
        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=current_user.id)
            db.add(hitung)

        # Ekstrak data dari response AI (Sesuaikan key-nya dengan format asli Tim 2 jika berbeda)
        is_match = hasil_validator.get("is_match", True)
        reasoning = hasil_validator.get("reasoning", str(hasil_validator))

        # Masukkan ke dalam kolom tabel
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