"""
FILE: app/config.py
DESKRIPSI:
Mengatur parameter konfigurasi utama aplikasi backend (seperti host, port, detail API AI),
serta inisialisasi dan pengaturan policy bucket penyimpanan pihak ketiga MinIO S3.
"""

import os
import boto3
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", 8000))
AI_BASE_URL = os.getenv("AI_BASE_URL")
MOCK_APP_HOST = os.getenv("MOCK_APP_HOST", "0.0.0.0")
MOCK_APP_PORT = int(os.getenv("MOCK_APP_PORT", 8001))
AI_BASE_URL = os.getenv("AI_BASE_URL")
AI_RUNPOD_URL = os.getenv("AI_RUNPOD_URL")
AI_RUNPOD_TOKEN = os.getenv("AI_RUNPOD_TOKEN")
API_TIM_3_URL = os.getenv("API_TIM_3_URL")

# --- KONFIGURASI MINIO (STORAGE) ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = "foto-rumah-warga"
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "localhost:9000")

def to_public_foto_url(url: str) -> str:
    """Konversi URL internal Docker (minio:9000) ke URL yang bisa diakses browser."""
    if not url or not MINIO_ENDPOINT:
        return url
    return url.replace(f"http://{MINIO_ENDPOINT}", f"http://{MINIO_PUBLIC_ENDPOINT}")

# Inisialisasi Klien S3/MinIO
s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

def ensure_bucket_exists():
    """Fungsi untuk memastikan bucket tersedia dan bisa diakses publik"""
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        s3_client.create_bucket(Bucket=MINIO_BUCKET)
        print(f"[MinIO] Bucket '{MINIO_BUCKET}' berhasil dibuat.")

    # Aturan agar foto bisa diakses (Read-Only) oleh siapapun (termasuk Frontend/AI)
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{MINIO_BUCKET}/*"]
            }
        ]
    }
    s3_client.put_bucket_policy(
        Bucket=MINIO_BUCKET,
        Policy=json.dumps(policy)
    )
    print(f"[MinIO] Policy PUBLIC Read-Only berhasil diterapkan pada bucket '{MINIO_BUCKET}'.")

# Eksekusi pengecekan bucket saat file config ini dipanggil
try:
    ensure_bucket_exists()
except Exception as e:
    print(f"[MinIO] Peringatan: Tidak bisa terhubung ke MinIO → {e}")