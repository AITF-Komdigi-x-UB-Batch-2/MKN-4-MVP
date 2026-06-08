"""
FILE: app/routers/asesmen.py
DESKRIPSI:
Menyediakan API untuk penilaian kelayakan sosial menggunakan RAG AI (Qwen di RunPod)
dan validasi kecocokan visual foto rumah warga (Tim 2).
"""

import httpx
import logging
import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_
import asyncio

from app import models
from app.database import get_db, SessionLocal
from app.security import get_current_user
from app.config import AI_BASE_URL, AI_RUNPOD_URL, API_TIM_3_URL
from app.schemas import item as item_schema

# Import Services & Utils
from app.services.task_queue import asesmen_queue
from app.services.ai_client import build_profil_warga, extract_rekomendasi, determine_eligibility

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/asesmen",
    tags=["4. Asesmen AI"]
)

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

    logger.info(f"[ASESMEN SOSIAL] Memulai analisis sosial untuk NIK: {keluarga.nik}, KK: {keluarga.no_kk}")
    hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()

    try:
        payload_llm = {
            "profil_warga": build_profil_warga(keluarga),
            "top_k": 5
        }
        logger.info(f"[ASESMEN SOSIAL] Profil warga berhasil dibentuk untuk LLM: {payload_llm['profil_warga'][:200]}...")

        headers_api = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # 1. Panggilan HTTP ke API Tim 3
        try:
            url_target = f"{API_TIM_3_URL}/recommend"
            logger.info(f"[ASESMEN SOSIAL] Mengirim request ke API Tim 3: {url_target}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url_target,
                    headers=headers_api,
                    json=payload_llm, 
                    timeout=60.0
                )
                response.raise_for_status()
                hasil_mentah = response.json()
                logger.info("[ASESMEN SOSIAL] Respon mentah diterima dari API Tim 3")
                
                # Fleksibilitas Ekstrak Balasan:
                if isinstance(hasil_mentah, str):
                    string_json_ai = hasil_mentah.strip().strip("```json").strip("```").strip()
                    hasil_final = json.loads(string_json_ai)
                elif isinstance(hasil_mentah, dict) and "choices" in hasil_mentah:
                    string_json_ai = hasil_mentah["choices"][0]["message"]["content"]
                    string_json_ai = string_json_ai.strip().strip("```json").strip("```").strip()
                    hasil_final = json.loads(string_json_ai)
                else:
                    hasil_final = hasil_mentah.get("justifikasi_dokumen", hasil_mentah)
                
                logger.info(f"[ASESMEN SOSIAL] Berhasil memparsing respon AI: {hasil_final}")
                    
        except Exception as e:
            logger.error(f"[ASESMEN SOSIAL] Gagal memanggil API Tim 3 (Sosial): {e}. Mengaktifkan Fallback Deterministik.")
            hasil_final = {
                "rekomendasi": determine_eligibility(keluarga),
                "ringkasan_profil": "Sistem menggunakan analisis cadangan (Fallback Deterministik) karena koneksi ke API AI Tim 3 terputus atau URL belum dikonfigurasi.",
                "rekomendasi_teknis_bansos": "Warga ini dievaluasi secara otomatis menggunakan sistem desil, usia lansia, dan filter disabilitas sesuai standar Juknis Jatim dasar tanpa analisis LLM."
            }

        rekomendasi_baru = extract_rekomendasi(hasil_final, keluarga)
        logger.info(f"[ASESMEN SOSIAL] Hasil ekstraksi rekomendasi baru: {rekomendasi_baru}")

        # Reasoning: simpan ringkasan + rekomendasi teknis dari Tim 3
        ringkasan = hasil_final.get("ringkasan_profil", "")
        teknis    = hasil_final.get("rekomendasi_teknis_bansos", "")
        analisis_rag = json.dumps(
            {"ringkasan_profil": ringkasan, "rekomendasi_teknis": teknis,
             "rekomendasi": hasil_final.get("rekomendasi", [])},
            ensure_ascii=False
        )

        bantuan_lama = None

        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=current_user.id)
            db.add(hitung)
        else:
            bantuan_lama = hitung.rekomendasi_bantuan

        # MENGHITUNG SKOR PADA SAAT ANALISIS BUKAN SAAT IMPOR
        from app.utils.scoring import hitung_skor_bantuan
        skor = hitung_skor_bantuan(keluarga)
        skor_pkh_val = skor.get("skor_pkh_plus") or 0.0
        skor_aspd_val = skor.get("skor_aspd") or 0.0
        
        # Override jika skor deterministik 0 di kedua program
        if skor_pkh_val <= 0.0 and skor_aspd_val <= 0.0:
            logger.info("[ASESMEN SOSIAL] Skor deterministik 0. Menganulir hasil AI dan menetapkan Tidak Eligible.")
            rekomendasi_baru = []

        is_eligible = len(rekomendasi_baru) > 0
        hitung.status_validasi = "validasi" if is_eligible else "ditolak"
        logger.info(f"[ASESMEN SOSIAL] Status validasi disetel menjadi: {hitung.status_validasi} (is_eligible: {is_eligible})")

        hitung.rekomendasi_bantuan = rekomendasi_baru
        hitung.reasoning_tim3 = analisis_rag
        
        hitung.skor_pkh_plus = skor_pkh_val
        hitung.skor_aspd = skor_aspd_val
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
            "justifikasi_dokumen": hasil_final
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
    logger.info(f"[ASESMEN VISUAL] Mengirim data ke validator visual Tim 2: {payload_ke_tim2}")

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
            reasoning = hasil_validator.get("reasoning", str(hasil_validator))
            logger.info(f"[ASESMEN VISUAL] Respon diterima dari Tim 2. IsMatch={is_match}, Reasoning={reasoning}")
    except Exception as e:
        logger.error(f"[ASESMEN VISUAL] Gagal terhubung ke server Tim 2: {e}. Mengaktifkan fallback visual.")
        is_match = True
        reasoning = f"Foto diasumsikan sesuai secara otomatis karena kendala sistem: {str(e)}"
        hasil_validator = {"is_match": True, "reasoning": reasoning}

    try:
        hitung = db.query(models.Perhitungan).filter(
            models.Perhitungan.keluarga_id == keluarga.id
        ).first()
        
        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=current_user.id)
            db.add(hitung)

        hitung.ada_ketidaksesuaian_visual = not is_match
        hitung.reasoning_tim2 = reasoning
        hitung.foto_id_digunakan = foto_utama.id

        logger.info(f"[ASESMEN VISUAL] Menyimpan hasil validasi visual ke DB untuk keluarga {keluarga.no_kk}. Match={is_match}")
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
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan data validasi visual: {str(e)}")

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
    # Set status ke proses agar frontend tahu data sedang diolah
    p = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == id_keluarga).first()
    if not p:
        p = models.Perhitungan(keluarga_id=id_keluarga, status_validasi="proses")
        db.add(p)
    else:
        p.status_validasi = "proses"
    db.commit()

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

async def background_batch_process(ids: list, user_id: str):
    logger.info(f"[BATCH ALL] Mulai memproses {len(ids)} data di background.")
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        for i, kid in enumerate(ids):
            try:
                logger.info(f"[BATCH ALL] [{i+1}/{len(ids)}] Memproses ID: {kid}")
                await asesmen_komprehensif_semua_tim(kid, user, db)
            except Exception as e:
                logger.error(f"[BATCH ALL] Gagal pada ID {kid}: {e}")
            await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"[BATCH ALL] Error fatal pada proses background: {e}")
    finally:
        db.close()
        logger.info(f"[BATCH ALL] Selesai memproses batch.")

@router.post("/batch-all", summary="Analisis seluruh antrean data secara background")
async def batch_all_analisis(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(models.Keluarga.id).outerjoin(
            models.Perhitungan, models.Perhitungan.keluarga_id == models.Keluarga.id
        ).filter(or_(
            models.Perhitungan.id.is_(None),
            models.Perhitungan.status_validasi == "analisis",
            models.Perhitungan.status_validasi.is_(None)
        )).all()
        
        ids = [row[0] for row in query]
        if not ids:
            return {"message": "Tidak ada data untuk dianalisis di tahap saat ini."}
            
        background_tasks.add_task(background_batch_process, ids, current_user.id)
        return {"message": f"Memulai analisis batch untuk {len(ids)} data di background."}
    except Exception as e:
        logger.error(f"[BATCH ALL] Gagal memulai endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
