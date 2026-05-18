import json
import boto3
from fastapi import FastAPI, Request, File, UploadFile, Form
import uvicorn
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="AI Server (AWS Bedrock Proxy)")

# 1. Konfigurasi AWS Bedrock sesuai arahan Mentor
bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# 2. Endpoint Tim 1 & 3 (Asesmen Sosial -> AWS Bedrock)
@app.post("/api/ai/jalur-sosial")
async def ai_sosial(request: Request):
    data_warga = await request.json()
    
    prompt_user = f"Berdasarkan data warga berikut: {json.dumps(data_warga)}. Tentukan apakah keluarga ini layak menerima bantuan sosial. Berikan rekomendasi spesifik (misal: PKH, Rutilahu, dll). Jawab WAJIB HANYA menggunakan format JSON dengan key 'rekomendasi_bantuan' (berisi array/list) dan 'justifikasi_dokumen' (berisi string penjelasan singkat)."
    
    body = json.dumps({
        "messages": [
            {
                "role": "system",
                "content": "Anda adalah asisten penilai kelayakan bantuan sosial. Anda patuh dan selalu menjawab murni dalam format JSON yang valid tanpa teks tambahan di luarnya."
            },
            {
                "role": "user",
                "content": prompt_user
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    })

    try:
        response = bedrock_client.invoke_model(
            modelId="google.gemma-3-4b-it",
            contentType="application/json",
            accept="application/json",
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        
        ai_reply = ""
        if "choices" in response_body:
            ai_reply = response_body["choices"][0]["message"]["content"]
        elif "outputs" in response_body:
            ai_reply = response_body["outputs"][0]["text"]
        else:
            ai_reply = str(response_body)

        ai_reply = ai_reply.replace("```json", "").replace("```", "").strip()
        
        try:
            hasil_json = json.loads(ai_reply)
            return hasil_json
        except json.JSONDecodeError:
            print(f"[Warning AWS]: AI tidak merespons dengan JSON murni. RAW: {ai_reply}")
            return {
                "rekomendasi_bantuan": ["Bantuan Sosial (Error Parsing)"],
                "justifikasi_dokumen": f"Analisis AI selesai, tetapi gagal diekstrak sebagai JSON. Raw response: {ai_reply[:200]}..."
            }

    except Exception as e:
        print(f"[ERROR AWS Bedrock]: {e}")
        return {
            "rekomendasi_bantuan": ["PKH (Mode Offline)"],
            "justifikasi_dokumen": f"Fallback Statis. Gagal menghubungi AWS Bedrock: {str(e)}"
        }

# 3. Endpoint Tim 2 (Visual Validator -> Tetap Mock Statis)
@app.post("/api/ai/visual-validator")
async def visual_validator(
    file: UploadFile = File(...),
    konteks_rumah: str = Form(default="Tidak ada konteks")
):
    print(f"[MOCK TIM 2] Menerima gambar: {file.filename} dengan kode material dinding: {konteks_rumah}")
    return {
        "is_match": True,
        "reasoning": f"Berdasarkan analisis visual AI statis, material dinding dengan kode {konteks_rumah} sangat identik dengan kondisi nyata pada foto rumah dari MinIO."
    }

if __name__ == "__main__":
    print("AI Proxy Server (Terhubung ke AWS Bedrock) menyala di Port 8001...")
    uvicorn.run(app, host="127.0.0.1", port=8001)