import httpx
import logging
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models
from app.config import AI_BASE_URL

logger = logging.getLogger(__name__)

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
        # Fallback jika tidak ada foto sama sekali
        hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga_id).first()
        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga_id, user_id=user_id)
            db.add(hitung)
        hitung.ada_ketidaksesuaian_visual = None
        hitung.reasoning_tim2 = "Validasi dilewati karena tidak ada foto rumah yang diunggah."
        db.commit()
        return {
            "status": "Dilewati",
            "reasoning": "Tidak ada foto rumah"
        }

    # Data survey hunian untuk dikirim ke Tim 2
    survey_data = {
        "atap_register": keluarga.atap or 0,
        "dinding_register": keluarga.dinding or 0,
        "lantai_register": keluarga.lantai or 0,
        "url_foto": foto_utama.url_foto
    }

    # Kirim ke REST API Tim 2 (Mock AI)
    payload_ke_tim2 = {
        "survey_data": survey_data,
        "is_pkh_or_aspd": True
    }

    try:
        async with httpx.AsyncClient() as client:
            res_ai = await client.post(
                f"{AI_BASE_URL}/api/v1/visual/validator",
                json=payload_ke_tim2,
                timeout=30.0
            )
            res_ai.raise_for_status()
            hasil_validator = res_ai.json()

        is_match = hasil_validator.get("is_match", True)
        reasoning = hasil_validator.get("reasoning", "Validasi visual selesai.")
    except Exception as e:
        logger.error("Gagal terhubung ke server Tim 2. Mengaktifkan fallback visual.", exc_info=True)
        is_match = True
        reasoning = f"Foto diasumsikan sesuai secara otomatis karena kendala sistem: {str(e)}"
        hasil_validator = {"is_match": True, "reasoning": reasoning}

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
