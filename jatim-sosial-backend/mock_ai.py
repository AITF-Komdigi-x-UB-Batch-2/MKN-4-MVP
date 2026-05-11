import os
import uvicorn
import asyncio
import random
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# PYDANTIC RESPONSE SCHEMAS
class JalurSosialResponse(BaseModel):
    """Response dari endpoint jalur-sosial (Tim 1 & Tim 3)"""
    status: str
    rekomendasi_bantuan: List[str]
    justifikasi_dokumen: str


class VisualValidatorResponse(BaseModel):
    """Response dari endpoint visual-validator (Tim 2)"""
    is_match: bool
    reasoning: str

# INISIALISASI FASTAPI
app = FastAPI(
    title="Mock AI Server",
    version="2.0",
    description="Mock server untuk menggantikan Tim 1, 2, dan 3"
)

# ENDPOINT TIM 1 & 3: JALUR SOSIAL (ANALISIS + RAG)
@app.post(
    "/api/ai/jalur-sosial",
    tags=["Tim 1 & 3 - Jalur Sosial"],
    summary="Analisis sosial ekonomi + RAG rekomendasi bantuan",
    response_model=JalurSosialResponse
)
async def mock_jalur_sosial(data_warga: dict = Body(...)):

    await asyncio.sleep(1.5)
    
    luas_lantai = data_warga.get("luas_lantai", 0)
    punya_motor = data_warga.get("aset_bergerak_sepeda_motor", False)
    punya_kulkas = data_warga.get("aset_bergerak_lemari_es", False)
    punya_tv = data_warga.get("aset_bergerak_tv_datar", False)
    nomor_kk = data_warga.get("nomor_kartu_keluarga", "UNKNOWN")

    rekomendasi = []
    justifikasi = []
    
    # Aturan 1: Sangat miskin (tidak ada aset utama)
    if not punya_motor and not punya_kulkas and not punya_tv:
        rekomendasi.append("Program Keluarga Harapan (PKH)")
        justifikasi.append("Keluarga terdeteksi sangat miskin - tidak memiliki aset motor, kulkas, atau TV")
    
    # Aturan 2: Rumah dengan luas lantai kecil
    if luas_lantai > 0 and luas_lantai < 20:
        rekomendasi.append("Bantuan Rutilahu (Rumah Tidak Layak Huni)")
        justifikasi.append(f"Luas lantai hanya {luas_lantai} m² (< 20 m²) - tidak memenuhi standar")
    
    # Aturan 3: Rentan miskin (punya beberapa aset tapi terbatas)
    if (punya_motor or punya_kulkas) and not punya_tv:
        rekomendasi.append("Bantuan Pangan Non Tunai (BPNT)")
        justifikasi.append("Keluarga tergolong rentan miskin - diberikan dukungan pangan")
    
    if not rekomendasi:
        rekomendasi = ["Monitoring dan Advokasi Sosial"]
        justifikasi.append("Keluarga tergolong mampu - diberikan monitoring berkala")

    alasan_lengkap = " | ".join(justifikasi) if justifikasi else "Analisis sosial ekonomi selesai"

    return {
        "status": "success",
        "rekomendasi_bantuan": rekomendasi,
        "justifikasi_dokumen": f"KK: {nomor_kk} → {alasan_lengkap}"
    }

# ENDPOINT TIM 2: VISUAL VALIDATOR (VALIDASI FOTO)
@app.post(
    "/api/ai/visual-validator",
    tags=["Tim 2 - Visual Validator"],
    summary="Validasi kesesuaian foto rumah dengan data sosial ekonomi",
    response_model=VisualValidatorResponse
)
async def mock_visual_validator(payload: dict = Body(...)):

    await asyncio.sleep(2)

    is_match = random.choice([True, True, True, False])
    
    image_url = payload.get("image_url", "")
    konteks = payload.get("konteks_rumah", {})
    
    jenis_lantai = konteks.get("jenis_lantai_terluas", "unknown")
    jenis_dinding = konteks.get("jenis_dinding_terluas", "unknown")
    jenis_atap = konteks.get("jenis_atap_terluas", "unknown")

    if is_match:
        alasan = (
            f"Foto SESUAI dengan data profil. "
            f"Kondisi visual rumah konsisten: lantai={jenis_lantai}, "
            f"dinding={jenis_dinding}, atap={jenis_atap}. "
            f"Status: TERVERIFIKASI"
        )
    else:
        alasan = (
            f"⚠️ Foto TIDAK SESUAI dengan data profil. "
            f"Terdapat inkonsistensi antara foto dan data sosial ekonomi yang tercatat. "
            f"Rekomendasi: Perlu verifikasi ulang lapangan."
        )
    
    confidence = round(random.uniform(0.85, 0.99), 2) if is_match else round(random.uniform(0.60, 0.79), 2)
    
    return {
        "is_match": is_match,
        "reasoning": alasan
    }

# HEALTH CHECK
@app.get("/health", tags=["Health"])
async def health_check():

    return {"status": "Mock AI Server is running..."}

if __name__ == "__main__":
    print("Menjalankan Mock Server AI di Port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)