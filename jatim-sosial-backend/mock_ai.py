import re
import json
import uvicorn
from fastapi import FastAPI, Request

app = FastAPI(
    title="Mock AI Server (Rule-Based dari Juknis)",
    description="Server simulasi AI yang otomatis membaca Umur dan Desil dari prompt untuk menentukan kelayakan PKH Plus atau ASPD."
)

# ==========================================
# 1. ENDPOINT TIM 3 (Asesmen Sosial - LLM Qwen3 Mock)
# ==========================================
@app.post("/api/chat") # Pastikan path ini sesuai dengan AI_RUNPOD_URL di asesmen.py
async def ai_sosial_mock(request: Request):
    payload = await request.json()
    
    # Ambil teks prompt yang dikirim oleh backend
    messages = payload.get("messages", [])
    user_content = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_content = msg.get("content", "")
            break

    # Ekstrak Umur dan Desil menggunakan Regex dari teks prompt
    umur_match = re.search(r"Umur\s*:\s*(\d+)", user_content, re.IGNORECASE)
    desil_match = re.search(r"Desil Nasional.*:\s*(\d+)", user_content, re.IGNORECASE)

    umur = int(umur_match.group(1)) if umur_match else 0
    desil = int(desil_match.group(1)) if desil_match else 10 # Default 10 jika tidak ketemu

    # Default Status
    pkh_status = "TIDAK LAYAK"
    aspd_status = "TIDAK LAYAK"
    alasan_pkh = "Tidak memenuhi syarat usia atau desil."
    alasan_aspd = "Tidak memenuhi syarat usia atau desil."
    demografi = f"Warga terdeteksi berusia {umur} tahun dan berada di Desil {desil}."

    # ---------------------------------------------------------
    # LOGIKA KELAYAKAN BERDASARKAN JUKNIS JATIM 2026
    # Hanya salah satu yang bisa LAYAK
    # ---------------------------------------------------------
    if umur >= 70 and desil <= 4:
        pkh_status = "LAYAK"
        alasan_pkh = "Memenuhi kriteria PKH Plus: Lansia >= 70 tahun dan berada di desil 1-4."
        alasan_aspd = "Bantuan dialokasikan untuk PKH Plus."
    
    elif umur <= 60 and desil <= 5:
        aspd_status = "LAYAK"
        alasan_pkh = "Bukan kategori Lansia >= 70 tahun."
        alasan_aspd = "Memenuhi kriteria prioritas ASPD: Usia <= 60 tahun dan berada di desil 1-5."
    
    else:
        # Jika umur 61-69 atau desil kaya
        alasan_pkh = "Usia atau kondisi ekonomi tidak memenuhi ambang batas PKH Plus."
        alasan_aspd = "Usia atau kondisi ekonomi tidak memenuhi ambang batas prioritas ASPD."

    # Rakit wujud JSON Evaluasi sesuai skema Tim 3
    laporan_evaluasi_json = {
        "laporan_evaluasi": {
            "kesimpulan": {
                "pkh_plus": {
                    "status_kelayakan": pkh_status,
                    "urgensi": "Tinggi" if pkh_status == "LAYAK" else "Tidak Ada",
                    "label": 1 if pkh_status == "LAYAK" else 0
                },
                "aspd": {
                    "status_kelayakan": aspd_status,
                    "urgensi": "Tinggi" if aspd_status == "LAYAK" else "Tidak Ada",
                    "label": 1 if aspd_status == "LAYAK" else 0
                }
            },
            "analisis": {
                "demografi": demografi,
                "sintesis_pkh_plus": alasan_pkh,
                "sintesis_aspd": alasan_aspd
            }
        }
    }

    # Bungkus menjadi format OpenAI/Runpod agar Backend FastAPI-mu bisa membacanya tanpa error
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(laporan_evaluasi_json)
                }
            }
        ]
    }


# ==========================================
# 2. ENDPOINT TIM 2 (Visual Validator)
# ==========================================
@app.post("/api/ai/visual-validator")
async def visual_validator_mock(request: Request):
    payload = await request.json()
    print(f"[DEBUG] Payload diterima untuk Visual Validator: Data Base64 masuk.")
    
    # Ambil konteks yang dikirim backend
    konteks = payload.get("konteks_rumah", {})
    jenis_lantai = konteks.get("jenis_lantai_terluas", "unknown")
    jenis_dinding = konteks.get("jenis_dinding_terluas", "unknown")
    jenis_atap = konteks.get("jenis_atap_terluas", "unknown")

    # Kembalikan response mock untuk Tim 2
    return {
        "is_match": True,
        "reasoning": f"Simulasi (Mock) Visual Selesai. Foto sesuai dengan data profil (lantai={jenis_lantai}, dinding={jenis_dinding}, atap={jenis_atap})."
    }

if __name__ == "__main__":
    print("AI Mock Server (Rule-Based Juknis) menyala di Port 8001...")
    uvicorn.run(app, host="127.0.0.1", port=8001)