import os
import httpx
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from uuid import UUID
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import models
import schemas
from database import engine, get_db
import csv
import io
import uvicorn
import json

# BAGIAN 1: SETUP AWAL
load_dotenv()
models.Base.metadata.create_all(bind=engine)

# BAGIAN 2: KONFIGURASI MINIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = "foto-rumah-warga"

s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

def ensure_bucket_exists():
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        s3_client.create_bucket(Bucket=MINIO_BUCKET)
        print(f"[MinIO] Bucket '{MINIO_BUCKET}' berhasil dibuat.")

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

try:
    ensure_bucket_exists()
except Exception as e:
    print(f"[MinIO] Peringatan: Tidak bisa terhubung ke MinIO → {e}")

# BAGIAN 3: KONFIGURASI KEAMANAN JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# BAGIAN 4: INISIALISASI APLIKASI FASTAPI
app = FastAPI(
    title="API Pemetaan Kemiskinan Jatim",
    version="2.1",
    description="Backend MVP Tim 4 — Mengorkestrasi alur data dari Tim 1, 2, dan 3."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI_BASE_URL = os.getenv("AI_BASE_URL")

# BAGIAN 5: DEPENDENCY — PENJAGA PINTU AUTENTIKASI
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:    

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token tidak memiliki identitas pengguna.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kadaluarsa.")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Pengguna tidak ditemukan.")
    return user

# BAGIAN 6: ENDPOINT AUTENTIKASI
@app.post("/auth/register", tags=["Auth"], summary="Registrasi user baru atau login jika sudah ada")
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):

    user_exist = db.query(models.User).filter(models.User.username == payload.username).first()
    
    if user_exist:
        return {
            "status": "Info",
            "pesan": f"Username '{payload.username}' sudah terdaftar. Silakan login ke akun Anda.",
            "action": "login"
        }

    email_exist = db.query(models.User).filter(models.User.email == payload.email).first()
    if email_exist:
        return {
            "status": "Info",
            "pesan": f"Email '{payload.email}' sudah terdaftar. Silakan login ke akun Anda.",
            "action": "login"
        }

    new_user = models.User(
        username=payload.username,
        email=payload.email,
        password_hash=get_password_hash(payload.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "status": "Sukses",
        "pesan": "Akun berhasil dibuat. Silakan login.",
        "username": new_user.username,
        "email": new_user.email,
        "action": "login"
    }

@app.post("/auth/login", tags=["Auth"], summary="Login dan dapatkan token JWT")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username atau password salah.")
    
    token = create_access_token(data={"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username
    }

# BAGIAN 7: IMPORT CSV (MASTER DATA & FOTO) - VERSI POP & LOG
@app.post(
    "/api/v1/import-csv",
    tags=["1. Import Master Data"],
    summary="Sinkronisasi data warga dan foto dari file CSV"
)
async def import_csv(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))

    kolom_sah = [c.name for c in models.Keluarga.__table__.columns]
    sukses = 0
    di_skip = 0
    log_foto = []

    # Kolom aset yang harus jadi INTEGER (0/1), bukan boolean
    KOLOM_ASET_INT = {
        "kepemilikan_aset",
        "aset_bergerak_tabung_gas", "aset_bergerak_lemari_es", "aset_bergerak_ac",
        "aset_bergerak_pemanas_air", "aset_bergerak_telepon_rumah", "aset_bergerak_tv_datar",
        "aset_bergerak_emas_perhiasan", "aset_bergerak_komputer_laptop_tablet",
        "aset_bergerak_sepeda_motor", "aset_bergerak_sepeda", "aset_bergerak_mobil",
        "aset_bergerak_perahu", "aset_bergerak_kapal_perahu_motor", "aset_bergerak_smartphone",
    }

    # Kolom yang harus jadi INTEGER
    KOLOM_INT = {
        "desil_nasional", "jumlah_anggota_keluarga", "jumlah_jenis_usaha",
        "jumlah_pekerja_dibayar", "jumlah_pekerja_tidak_dibayar",
        "luas_lantai_bangunan", "id_dayapenerangan",
        "lahan_tempat_lain", "rumah_tempat_lain",
        "jml_sapi", "jml_kerbau", "jml_kuda", "jml_babi", "jml_kambing_domba",
    }

    def safe_int(v, default=0):
        try:
            return int(float(v)) if v and str(v).strip() not in ("", "nan") else default
        except (ValueError, TypeError):
            return default

    def fix_nik(v):
        """Konversi scientific notation '3.57301E+15' → '357301XXXXXXX'"""
        if not v:
            return None
        try:
            # Jika berupa scientific notation, konversi ke integer lalu string
            return str(int(float(v)))
        except (ValueError, TypeError):
            return str(v).strip()

    async with httpx.AsyncClient() as client:
        for row in reader:
            try:
                no_kk_row = row.get("no_kk")
                if not no_kk_row:
                    di_skip += 1
                    continue

                # BUG FIX #3: Case-insensitive pop untuk kolom foto
                # CSV punya 'Foto_rumah_tampak_dalam', bukan 'Foto_Rumah_Tampak_Dalam'
                tampak_luar_raw_urls  = row.pop("foto_rumah", "")
                tampak_dalam_raw_urls = row.pop("foto_rumah_tampak_dalam", "")  # ← huruf kecil

                # 1. Bersihkan Data Keluarga
                data_bersih = {}
                for k, v in row.items():
                    if k not in kolom_sah:
                        continue

                    val_str = str(v).strip().upper() if v and str(v).strip() not in ("", "nan") else ""

                    # BUG FIX #1: aset → INTEGER (0/1), bukan bool
                    if k in KOLOM_ASET_INT:
                        data_bersih[k] = 1 if val_str in ("YA", "1", "TRUE") else 0

                    # BUG FIX #2: nik & no_kk → string bersih dari scientific notation
                    elif k in ("nik", "no_kk"):
                        data_bersih[k] = fix_nik(v)

                    elif k.startswith("kode_"):
                        data_bersih[k] = val_str.replace(".", "") if val_str else None

                    elif k in KOLOM_INT:
                        data_bersih[k] = safe_int(v)

                    else:
                        data_bersih[k] = v if v and str(v).strip() not in ("", "nan") else None

                # 2. Cek Idempotensi & History
                keluarga_lama = db.query(models.Keluarga).filter(
                    models.Keluarga.no_kk == data_bersih.get("no_kk")
                ).first()

                if keluarga_lama:
                    data_histori = {c.name: getattr(keluarga_lama, c.name) for c in models.Keluarga.__table__.columns}
                    data_histori.pop("id", None)
                    data_histori["keluarga_id"] = keluarga_lama.id

                    arsip_baru = models.KeluargaHistory(**data_histori)
                    db.add(arsip_baru)

                    for k, v in data_bersih.items():
                        setattr(keluarga_lama, k, v)
                    keluarga_diproses = keluarga_lama
                else:
                    keluarga_baru = models.Keluarga(**data_bersih)
                    db.add(keluarga_baru)
                    keluarga_diproses = keluarga_baru

                db.flush()

                # 3. Proses URL Foto
                for tipe, raw_urls in [("tampak_luar", tampak_luar_raw_urls), ("tampak_dalam", tampak_dalam_raw_urls)]:
                    if not raw_urls:
                        log_foto.append(f"KK {no_kk_row}: Kolom foto '{tipe}' kosong.")
                        continue

                    for index, original_url in enumerate(u.strip() for u in raw_urls.split(",") if u.strip()):
                        try:
                            foto_ada = db.query(models.Foto).filter(
                                models.Foto.keluarga_id == keluarga_diproses.id,
                                models.Foto.nama_file_asli == original_url
                            ).first()

                            if not foto_ada:
                                foto_res = await client.get(original_url, follow_redirects=True, timeout=10.0)
                                if foto_res.status_code == 200:
                                    nama_file_minio = f"{keluarga_diproses.id}_{tipe}_{index}.jpg"
                                    s3_client.put_object(
                                        Bucket=MINIO_BUCKET,
                                        Key=nama_file_minio,
                                        Body=foto_res.content,
                                        ContentType="image/jpeg"
                                    )
                                    url_minio_final = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{nama_file_minio}"
                                    db.add(models.Foto(
                                        keluarga_id=keluarga_diproses.id,
                                        url_foto=url_minio_final,
                                        sumber="dataset_csv",
                                        nama_file_asli=original_url,
                                        tampak_dalam=(tipe == "tampak_dalam")
                                    ))
                                    log_foto.append(f"KK {no_kk_row}: BERHASIL upload foto {tipe}")
                                else:
                                    log_foto.append(f"KK {no_kk_row}: Gagal download foto {tipe} (HTTP {foto_res.status_code})")
                        except Exception as e:
                            log_foto.append(f"KK {no_kk_row}: ERROR foto {tipe} → {str(e)}")

                sukses += 1

            except Exception as e:
                # BUG FIX #4: Rollback session agar baris berikutnya tidak kena PendingRollbackError
                db.rollback()
                di_skip += 1
                log_foto.append(f"Error fatal baris KK {row.get('no_kk', '?')}: {str(e)}")
                continue

    db.commit()

    return {
        "status": "Sukses",
        "pesan": f"{sukses} data keluarga berhasil disinkronisasi, {di_skip} baris dilewati.",
        "log_proses_foto": log_foto
    }

# BAGIAN 8: ASESMEN SOSIAL — TIM 1 & TIM 3
@app.post(
    "/api/v1/asesmen/sosial",
    tags=["2. Asesmen Tim 1 & 3"],
    summary="Analisis Tim 1 yang diteruskan ke Tim 3"
)
async def asesmen_sosial(
    payload: schemas.TriggerAsesmenRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keluarga = db.query(models.Keluarga).filter(
        models.Keluarga.id == payload.keluarga_id
    ).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")

    try:
        data_untuk_ai = {
            c.name: getattr(keluarga, c.name)
            for c in models.Keluarga.__table__.columns
        }
        data_untuk_ai.pop("id", None)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{AI_BASE_URL}/api/ai/jalur-sosial",
                    json=data_untuk_ai,
                    timeout=30.0
                )
                response.raise_for_status()
                hasil_final = response.json()
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Gagal mendapatkan analisis dari jalur AI: {e}")

        rekomendasi_baru = hasil_final.get("rekomendasi_bantuan", [])
        analisis_rag = hasil_final.get("justifikasi_dokumen", "")

        hitung = db.query(models.Perhitungan).filter(
            models.Perhitungan.keluarga_id == keluarga.id
        ).first()

        bantuan_lama = None

        if not hitung:
            hitung = models.Perhitungan(
                keluarga_id=keluarga.id,
                user_id=current_user.id
            )
            db.add(hitung)
        else:
            bantuan_lama = hitung.rekomendasi_bantuan

        hitung.rekomendasi_bantuan = rekomendasi_baru
        hitung.reasoning_tim3 = analisis_rag

        log = models.LogHistori(
            keluarga_id=keluarga.id,
            user_id=current_user.id,
            desil_lama=None,
            desil_baru=None,
            bantuan_lama=bantuan_lama,
            bantuan_baru=rekomendasi_baru
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

# BAGIAN 9: ASESMEN VISUAL — TIM 2
@app.post(
    "/api/v1/asesmen/visual/{id_keluarga}",
    tags=["3. Asesmen Tim 2"],
    summary="Trigger AI Visual mengirim URL dan ID ke Tim 2"
)
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

    url_foto_luar = foto_tampak_luar.url_foto if foto_tampak_luar else None
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

        # 4. Tangkap Response Bersarang (Nested JSON) dari Tim 2
        hitung = db.query(models.Perhitungan).filter(
            models.Perhitungan.keluarga_id == keluarga.id
        ).first()
        
        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=current_user.id)
            db.add(hitung)

        db.commit()

        return {
            "status": "Sukses",
            "hasil_tim2": hasil_validator
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Kesalahan koneksi ke Tim 2: {str(e)}")

# BAGIAN 10: ENDPOINT READ DATA (GET)
@app.get(
    "/api/v1/keluarga",
    tags=["4. Read Data"],
    summary="Ambil daftar semua keluarga (dengan pagination)"
)
async def list_keluarga(
    skip: int = 0,
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    total = db.query(models.Keluarga).count()
    data = db.query(models.Keluarga).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [schemas.KeluargaResponse.from_orm(k) for k in data]
    }

@app.get(
    "/api/v1/keluarga/{keluarga_id}",
    tags=["4. Read Data"],
    summary="Ambil detail satu keluarga berdasarkan ID"
)
async def get_keluarga(
    keluarga_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keluarga = db.query(models.Keluarga).filter(
        models.Keluarga.id == keluarga_id
    ).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data keluarga tidak ditemukan.")

    foto_terbaru = db.query(models.Foto).filter(
        models.Foto.keluarga_id == keluarga_id
    ).order_by(models.Foto.diunggah_pada.desc()).first()
    
    url_public = foto_terbaru.url_foto if foto_terbaru else None

    return {
        "keluarga": schemas.KeluargaResponse.from_orm(keluarga),
        "foto_url_public": url_public
    }

@app.get(
    "/api/v1/keluarga/{keluarga_id}/histori",
    tags=["4. Read Data"],
    summary="Lihat riwayat perubahan asesmen satu keluarga"
)
async def get_histori(
    keluarga_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    logs = db.query(models.LogHistori).filter(
        models.LogHistori.keluarga_id == keluarga_id
    ).order_by(models.LogHistori.timestamp.desc()).all()

    return {
        "keluarga_id": str(keluarga_id),
        "jumlah_riwayat": len(logs),
        "riwayat": [
            {
                "timestamp": log.timestamp,
                "desil_lama": log.desil_lama,
                "desil_baru": log.desil_baru,
                "bantuan_lama": log.bantuan_lama,
                "bantuan_baru": log.bantuan_baru,
            }
            for log in logs
        ]
    }

if __name__ == "__main__":
    print("Menjalankan Main Server di Port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)