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
    summary="Validasi kesesuaian foto rumah dengan data sosial ekonomi (Format TOON - DUMMY)"
)
async def mock_visual_validator(payload: dict = Body(...)):
    # 1. Ekstrak teks dari dalam array payload OpenAI Tim 2
    messages = payload.get("messages", [])
    user_text = ""
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "text" and "DATA REFERENSI DTSEN" in item.get("text", ""):
                        user_text = item.get("text")
                        break
            elif isinstance(content, str):
                user_text = content

    # 2. Parsing label aktual dari prompt user agar dummy tidak kosong
    jenis_atap = "Tidak terdeteksi"
    jenis_dinding = "Tidak terdeteksi"
    jenis_lantai = "Tidak terdeteksi"

    if user_text:
        m_atap = re.search(r"Atap\s*:\s*(.+)", user_text)
        m_dinding = re.search(r"Dinding\s*:\s*(.+)", user_text)
        m_lantai = re.search(r"Lantai\s*:\s*(.+)", user_text)
        
        if m_atap: jenis_atap = m_atap.group(1).strip()
        if m_dinding: jenis_dinding = m_dinding.group(1).strip()
        if m_lantai: jenis_lantai = m_lantai.group(1).strip()

    # 3. Tentukan secara acak apakah simulasi ini Sesuai atau Tidak Sesuai (75% Sesuai)
    is_match = random.choice([True, True, True, False])
    status_simulasi = "Sesuai" if is_match else "Tidak sesuai"

    # 4. Generate Alasan Toon (Pure Dummy / Hardcode)
    alasan_toon = (
        f"Hasil[3]{{Komponen,Prediksi,Status,Alasan}}:\n"
        f"Atap,{jenis_atap},{status_simulasi},\"Mock AI: Evaluasi visual untuk atap menunjukkan kondisi {status_simulasi.lower()}.\"\n"
        f"Dinding,{jenis_dinding},{status_simulasi},\"Mock AI: Evaluasi visual untuk dinding menunjukkan kondisi {status_simulasi.lower()}.\"\n"
        f"Lantai,{jenis_lantai},{status_simulasi},\"Mock AI: Evaluasi visual untuk lantai menunjukkan kondisi {status_simulasi.lower()}.\""
    )

    # 5. Mengembalikan payload persis struktur JSON dari OpenAI/RunPod
    return {
        "id": "chatcmpl-mock-vision-dummy",
        "object": "chat.completion",
        "created": 1717000000,
        "model": "model-vision-tim-2-dummy",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": alasan_toon
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 75,
            "total_tokens": 225
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "Mock AI Server for Tim 2 (Dummy Mode) is running..."}


if __name__ == "__main__":
    print("Menjalankan Server AI Mock Dummy Tim 2 di Port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)