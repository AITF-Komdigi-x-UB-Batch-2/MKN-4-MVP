import os
import json
import uvicorn
import asyncio
import random
from fastapi import FastAPI, Body, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.config import MOCK_APP_HOST, MOCK_APP_PORT

# PYDANTIC RESPONSE SCHEMAS
class JalurSosialResponse(BaseModel):
    status: str
    ringkasan_data: Optional[str] = None
    rekomendasi_bantuan: List[str]
    justifikasi_dokumen: str
    skor_aspd: float
    skor_pkh_plus: float

class VisualValidatorResponse(BaseModel):
    is_match: bool
    reasoning: str

# KAMUS SKENARIO JALUR SOSIAL (Berdasarkan 10 baris df_sample_10_tanpa_skor.csv)
SKENARIO_JALUR_SOSIAL = {
    "FAM_8d03a0167c237e46a1857dc7e9da9bc77bf9a9cd9fccc401a534637f78d063e7": {
        "status": "Sangat Miskin",
        "ringkasan_data": "Keluarga lansia tunggal (Desil 1), tidak memiliki aset produktif.",
        "rekomendasi_bantuan": ["PKH Plus"],
        "justifikasi_dokumen": "Kepala keluarga berusia > 70 tahun dan hidup sendiri tanpa penghasilan tetap. Sangat memenuhi kriteria pemenuhan kebutuhan dasar lansia.",
        "skor_pkh_plus": 95.50,
        "skor_aspd": 0.00
    },
    "FAM_1b13ec6def5164300b981b40f54ea1264847b41c31255b985d79030fe06ad297": {
        "status": "Sangat Miskin",
        "ringkasan_data": "Keluarga dengan anggota penyandang disabilitas fisik berat (Desil 1).",
        "rekomendasi_bantuan": ["ASPD"],
        "justifikasi_dokumen": "Terdapat anggota keluarga dengan disabilitas menetap yang menghambat fungsi sosial ekonomi. Prioritas dialokasikan untuk ASPD.",
        "skor_pkh_plus": 0.00,
        "skor_aspd": 98.00
    },
    "FAM_618a7fd66d04711722c78de81dc422fdbf589fb2ef7daf2ee82406112c937b04": {
        "status": "Sangat Miskin",
        "ringkasan_data": "Terdapat lansia risiko tinggi dan anak penyandang disabilitas.",
        "rekomendasi_bantuan": ["PKH Plus", "ASPD"],
        "justifikasi_dokumen": "Keluarga mengalami kerentanan berlapis. Dokumen memvalidasi lansia non-produktif sekaligus anak berkebutuhan khusus. Direkomendasikan menerima intervensi ganda.",
        "skor_pkh_plus": 90.00,
        "skor_aspd": 92.00
    },
    "FAM_1795edb5bb1d6f2a3decbe782e7e0ec21e0538d27e31cc7a9fb2dbffd9f59a58": {
        "status": "Mampu",
        "ringkasan_data": "Keluarga desil atas (Desil 9), memiliki kendaraan roda empat.",
        "rekomendasi_bantuan": [],
        "justifikasi_dokumen": "Indikator ekonomi berada jauh di atas ambang batas. Tidak terdapat komponen lansia rentan ataupun disabilitas berat di dalam KK.",
        "skor_pkh_plus": 0.00,
        "skor_aspd": 0.00
    },
    "FAM_34e30f5db8fffe0fba5126227e6485c9f8894cd74fe3ec3f174795b519d1ce8a": {
        "status": "Mampu",
        "ringkasan_data": "NIK terdaftar di database kepegawaian negara.",
        "rekomendasi_bantuan": [],
        "justifikasi_dokumen": "Sistem anomali mendeteksi kepala keluarga adalah aparatur negara aktif. Status kelayakan DTKS harus dicabut.",
        "skor_pkh_plus": 0.00,
        "skor_aspd": 0.00
    },
    "FAM_a4d364dc0317f7e70c8ac415897a36857830a47a1c0ea81b6c285b33d33c7aad": {
        "status": "Sangat Miskin",
        "ringkasan_data": "Lansia dengan riwayat penyakit kronis (bedridden).",
        "rekomendasi_bantuan": ["PKH Plus"],
        "justifikasi_dokumen": "Kondisi fisik lansia sangat rentan dan membutuhkan perawatan medis lanjutan. Bantuan PKH Plus sangat diwajibkan.",
        "skor_pkh_plus": 98.50,
        "skor_aspd": 10.00
    },
    "FAM_ffc29cb34ffb057b72662448f77558255e8f87a101a7b4efdddb11d08a649d0e": {
        "status": "Miskin",
        "ringkasan_data": "Lansia berperan sebagai wali tunggal untuk balita.",
        "rekomendasi_bantuan": ["PKH Plus"],
        "justifikasi_dokumen": "Terdapat beban ekonomi berat pada lansia yang harus mengasuh cucu. Intervensi PKH Plus krusial untuk mencegah penelantaran.",
        "skor_pkh_plus": 88.00,
        "skor_aspd": 0.00
    },
    "FAM_cc5bec281b27b722dc416c8cb854b99f8f214d35633da0c7f29c131ea71e6059": {
        "status": "Rentan Miskin",
        "ringkasan_data": "Lansia perempuan (65 tahun) bekerja sebagai buruh tani lepas.",
        "rekomendasi_bantuan": ["PKH Plus"],
        "justifikasi_dokumen": "Meski masih bekerja, usia dan jenis pekerjaan tidak memberikan keamanan finansial. Layak mendapat jaring pengaman PKH Plus.",
        "skor_pkh_plus": 75.00,
        "skor_aspd": 0.00
    },
    "FAM_65accd0e8dbc8d1ac09579847057630aeb981b8017c88a61d8b45ef8686575c0": {
        "status": "Sangat Miskin",
        "ringkasan_data": "Anak di bawah umur memiliki disabilitas intelektual dan fisik.",
        "rekomendasi_bantuan": ["ASPD"],
        "justifikasi_dokumen": "Kasus disabilitas ganda membutuhkan biaya terapi dan perawatan tinggi. Skor kelayakan ASPD maksimal.",
        "skor_pkh_plus": 0.00,
        "skor_aspd": 99.00
    },
    "FAM_a958a3570c3ad72d58563b72a75aea65c178aa5cc30fd5c623f9fb29fcff6bc2": {
        "status": "Miskin",
        "ringkasan_data": "Pasangan muda berpenghasilan di bawah UMR (Desil 3).",
        "rekomendasi_bantuan": ["BPNT"],
        "justifikasi_dokumen": "Keluarga miskin namun tidak masuk kriteria khusus Lansia/Disabilitas. Bantuan diarahkan ke pemenuhan sembako (BPNT).",
        "skor_pkh_plus": 5.00,
        "skor_aspd": 0.00
    }
}


# INISIALISASI FASTAPI
app = FastAPI(
    title="Mock AI Server (Hybrid Fallback)",
    version="2.0",
    description="Server Mock AI Jatim Sosial — Menggunakan skenario statis untuk testing CSV, dan fallback dinamis untuk data lainnya."
)

# ENDPOINT TIM 1 & 3: JALUR SOSIAL
@app.post(
    "/api/ai/jalur-sosial",
    tags=["Tim 1 & 3 - Jalur Sosial"],
    summary="Analisis sosial ekonomi statis (Mock Hybrid)",
    response_model=JalurSosialResponse
)
async def mock_jalur_sosial(data_warga: dict = Body(...)):
    print("[Mock] Menerima request untuk Jalur Sosial. Memproses...")
    await asyncio.sleep(1.0) # Simulasi delay jaringan/pemrosesan
    
    nomor_kk = data_warga.get("no_kk", "UNKNOWN")

    # 1. CEK SKENARIO: Jika no_kk ada di dalam daftar CSV
    if nomor_kk in SKENARIO_JALUR_SOSIAL:
        print(f"[Mock] Skenario spesifik ditemukan untuk KK: {nomor_kk[:10]}...")
        return SKENARIO_JALUR_SOSIAL[nomor_kk]
    
    # 2. FALLBACK: Jika no_kk tidak ada di daftar CSV, gunakan aturan statis
    print(f"[Mock] Skenario spesifik tidak ditemukan. Memakai aturan fallback statis...")
    luas_lantai = data_warga.get("luas_lantai", 0)
    punya_motor = data_warga.get("aset_bergerak_sepeda_motor", False)
    punya_kulkas = data_warga.get("aset_bergerak_lemari_es", False)
    punya_tv = data_warga.get("aset_bergerak_tv_datar", False)

    rekomendasi = []
    justifikasi = []
    status_kemiskinan = "Mampu"
    
    # Aturan 1: Sangat miskin
    if not punya_motor and not punya_kulkas and not punya_tv:
        rekomendasi.append("Program Keluarga Harapan (PKH)")
        justifikasi.append("Keluarga terdeteksi sangat miskin - tidak memiliki aset motor, kulkas, atau TV.")
        status_kemiskinan = "Sangat Miskin"
    
    # Aturan 2: Rumah dengan luas lantai kecil
    if luas_lantai > 0 and luas_lantai < 20:
        rekomendasi.append("Bantuan Rutilahu (Rumah Tidak Layak Huni)")
        justifikasi.append(f"Luas lantai hanya {luas_lantai} m² (< 20 m²) - tidak memenuhi standar layak huni.")
        if status_kemiskinan != "Sangat Miskin":
             status_kemiskinan = "Rentan Miskin"
    
    # Aturan 3: Rentan miskin
    if (punya_motor or punya_kulkas) and not punya_tv:
        rekomendasi.append("Bantuan Pangan Non Tunai (BPNT)")
        justifikasi.append("Keluarga tergolong rentan miskin - diberikan dukungan pangan.")
        if status_kemiskinan != "Sangat Miskin":
             status_kemiskinan = "Rentan Miskin"
    
    if not rekomendasi:
        rekomendasi = ["Monitoring dan Advokasi Sosial"]
        justifikasi.append("Keluarga tergolong mampu secara kepemilikan aset - diberikan monitoring berkala.")

    alasan_lengkap = " | ".join(justifikasi) if justifikasi else "Analisis sosial ekonomi statis selesai."
    
    return {
        "status": status_kemiskinan,
        "ringkasan_data": "Data tidak termasuk dalam skenario uji coba CSV.",
        "rekomendasi_bantuan": rekomendasi,
        "justifikasi_dokumen": f"KK: {nomor_kk} → {alasan_lengkap}",
        "skor_aspd": round(random.uniform(20.0, 95.0), 2),
        "skor_pkh_plus": round(random.uniform(20.0, 95.0), 2)
    }

# ENDPOINT TIM 2: VISUAL VALIDATOR
@app.post(
    "/api/ai/visual-validator",
    tags=["Tim 2 - Visual Validator"],
    summary="Validasi kesesuaian foto rumah statis (Mock)",
    response_model=VisualValidatorResponse
)
async def mock_visual_validator(payload: dict = Body(...)):
    print("[Mock] Menerima request untuk Visual Validator. Memproses secara statis...")
    await asyncio.sleep(1.0) # Simulasi delay jaringan/pemrosesan
    
    konteks = payload.get("konteks_rumah", {})
    jenis_lantai = konteks.get("jenis_lantai_terluas", "unknown")
    jenis_dinding = konteks.get("jenis_dinding_terluas", "unknown")
    jenis_atap = konteks.get("jenis_atap_terluas", "unknown")

    # Ambil random kecocokan (75% True, 25% False) untuk simulasi
    is_match = random.choice([True, True, True, False])

    if is_match:
        alasan_dinamis = (
            f"Foto SESUAI dengan data profil. "
            f"Kondisi visual rumah konsisten: lantai={jenis_lantai}, "
            f"dinding={jenis_dinding}, atap={jenis_atap}. "
            f"Status: TERVERIFIKASI."
        )
    else:
        alasan_dinamis = (
            f"Foto TIDAK SESUAI dengan data profil. "
            f"Terdapat inkonsistensi visual yang signifikan antara foto dan data sosial ekonomi yang tercatat "
            f"(lantai={jenis_lantai}, dinding={jenis_dinding}, atap={jenis_atap}). "
            f"Rekomendasi: Perlu verifikasi ulang lapangan."
        )

    return {
        "is_match": is_match,
        "reasoning": alasan_dinamis
    }

# HEALTH CHECK
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "Mock AI Server (Hybrid) is running..."}

if __name__ == "__main__":
    print(f"Menjalankan Server Mock AI Jatim Sosial di {MOCK_APP_HOST}:{MOCK_APP_PORT}...")
    uvicorn.run(app, host=MOCK_APP_HOST, port=MOCK_APP_PORT)