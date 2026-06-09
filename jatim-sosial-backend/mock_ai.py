import re
import uvicorn
import random
from fastapi import FastAPI, Body

# INISIALISASI FASTAPI (KHUSUS TIM 2 - PURE DUMMY)
app = FastAPI(
    title="Mock AI Server - Tim 2 (Dummy Mode)",
    version="4.2",
    description="Server Mock murni statis khusus untuk Tim 2 (Visual Validator). Menghasilkan format TOON tanpa memanggil API eksternal."
)

# =====================================================================
# ENDPOINT TIM 2 (MENGGUNAKAN STANDAR TOON & OPENAI)
# =====================================================================
@app.post(
    "/api/ai/visual-validator",
    tags=["Tim 2 - Visual Validator"],
    summary="Validasi kesesuaian foto rumah dengan data sosial ekonomi (Format JSON Langsung)"
)
async def mock_visual_validator(payload: dict = Body(...)):
    # 1. Ekstrak data dari payload baru (sesuai schema di asesmen.py)
    id_data = payload.get("id_data", "Unknown")
    id_atap = payload.get("id_atap_terluas", 0)
    id_dinding = payload.get("id_dinding_terluas", 0)
    id_lantai = payload.get("id_lantai_terluas", 0)
    
    # 2. Pemetaan dummy ID ke nama bahan (hanya untuk log/reasoning dummy)
    atap_map = {1: "Beton", 2: "Genteng", 3: "Seng", 4: "Asbes", 5: "Bambu", 6: "Jerami", 0: "Tidak terdeteksi"}
    dinding_map = {1: "Tembok", 2: "Kayu", 3: "Bambu", 4: "Tanah", 0: "Tidak terdeteksi"}
    lantai_map = {1: "Keramik", 2: "Semen", 3: "Kayu", 4: "Tanah", 0: "Tidak terdeteksi"}

    jenis_atap = atap_map.get(int(id_atap) if id_atap else 0, "Tidak terdeteksi")
    jenis_dinding = dinding_map.get(int(id_dinding) if id_dinding else 0, "Tidak terdeteksi")
    jenis_lantai = lantai_map.get(int(id_lantai) if id_lantai else 0, "Tidak terdeteksi")

    # 3. Tentukan secara acak apakah simulasi ini Sesuai atau Tidak Sesuai (75% Sesuai)
    is_match = random.choice([True, True, True, False])
    status_simulasi = "Sesuai" if is_match else "Tidak sesuai"

    # 4. Generate Alasan
    alasan_teks = (
        f"Mock AI: Evaluasi visual terhadap gambar menunjukkan:\n"
        f"- Atap terdeteksi berbahan {jenis_atap} ({status_simulasi})\n"
        f"- Dinding terdeteksi berbahan {jenis_dinding} ({status_simulasi})\n"
        f"- Lantai terdeteksi berbahan {jenis_lantai} ({status_simulasi})\n"
        f"Kesimpulan akhir: {'Sesuai' if is_match else 'Terdapat ketidaksesuaian'} dengan data administratif."
    )

    # 5. Kembalikan sesuai format yang diharapkan oleh asesmen.py
    return {
        "status": "success",
        "id_data": id_data,
        "is_match": is_match,
        "reasoning": alasan_teks
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "Mock AI Server for Tim 2 (Dummy Mode) is running..."}


if __name__ == "__main__":
    print("Menjalankan Server AI Mock Dummy Tim 2 di Port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)