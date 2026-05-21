import os
import httpx
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import boto3
from dotenv import load_dotenv
import models
from database import engine, get_db
import csv
import io
import json

# 1. SETUP AWAL
load_dotenv()
models.Base.metadata.create_all(bind=engine)

# 2. KONFIGURASI MINIO
MINIO_ENDPOINT = "127.0.0.1:9000"
MINIO_ACCESS_KEY = "admin_minio"
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = "foto-rumah-warga"

s3_client = boto3.client(
    "s3", endpoint_url=f"http://{MINIO_ENDPOINT}",
   aws_access_key_id=MINIO_ACCESS_KEY, aws_secret_access_key=MINIO_SECRET_KEY,
)

# 3. KEAMANAN JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "rahasia_aman")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password, hashed_password): return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password): return pwd_context.hash(password)
def create_access_token(data: dict): return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

app = FastAPI(title="API Pemetaan Kemiskinan Jatim", version="2.0 (Final Workshop)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# 4. SCHEMAS
class DataWarga(BaseModel):
    kode_provinsi: str = Field(..., max_length=10)
    provinsi: str = Field(..., max_length=100)
    kode_kabupaten_kota: str = Field(..., max_length=15)
    kabupaten_kota: str = Field(..., max_length=100)
    kode_kecamatan: str = Field(..., max_length=20)
    kecamatan: str = Field(..., max_length=100)
    kode_kelurahan_desa: str = Field(..., max_length=25)
    kelurahan_desa: str = Field(..., max_length=100)
    alamat: str = Field(..., max_length=500)
    nomor_kartu_keluarga: str = Field(..., max_length=16)
    jumlah_anggota_keluarga: int
    nama_anggota_keluarga: str = Field(..., max_length=500)
    pbi_nas: bool
    pbi_pemda: bool
    id_pelanggan_pln: Optional[str] = None
    status_kepemilikan_rumah: int
    jenis_lantai_terluas: int
    luas_lantai: int
    jenis_dinding_terluas: int
    jenis_atap_terluas: int
    sumber_air_minum_utama: int
    sumber_penerangan_utama: int
    daya_terpasang: int
    bahan_bakar_utama_memasak: int
    fasilitas_bab: int
    jenis_kloset: int
    pembuangan_akhir_tinja: int
    kepemilikan_aset: bool
    aset_bergerak_tabung_gas: bool
    aset_bergerak_lemari_es: bool
    aset_bergerak_ac: bool
    aset_bergerak_pemanas_air: bool
    aset_bergerak_telepon_rumah: bool
    aset_bergerak_tv_datar: bool
    aset_bergerak_emas_perhiasan: bool
    aset_bergerak_komputer_laptop_tablet: bool
    aset_bergerak_sepeda_motor: bool
    aset_bergerak_sepeda: bool
    aset_bergerak_mobil: bool
    aset_bergerak_perahu: bool
    aset_bergerak_kapal_perahu_motor: bool
    aset_bergerak_smartphone: bool
    aset_tidak_bergerak_lahan_lainnya: bool
    aset_tidak_bergerak_rumah_lainnya: bool
    jumlah_ternak_sapi: int
    jumlah_ternak_kerbau: int
    jumlah_ternak_kuda: int
    jumlah_ternak_babi: int
    jumlah_ternak_kambing_domba: int
    skor: Optional[int] = None
    desil_nasional: Optional[int] = None

# 5. AUTHENTICATION
@app.post("/auth/buat-admin", tags=["Auth"])
def buat_admin(db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == "admin_jatim").first(): return {"pesan": "Sudah ada!"}
    db.add(models.User(username="admin_jatim", email="admin@dinsos.go.id", password_hash=get_password_hash("taritsa123")))
    db.commit()
    return {"pesan": "Admin dibuat"}

@app.post("/auth/login", tags=["Auth"])
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash): raise HTTPException(status_code=401, detail="Salah!")
    return {"access_token": create_access_token(data={"sub": user.username, "exp": datetime.utcnow() + timedelta(minutes=60)}), "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try: payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError: raise HTTPException(status_code=401, detail="Token Invalid")
    user = db.query(models.User).filter(models.User.username == payload.get("sub")).first()
    if not user: raise HTTPException(status_code=401)
    return user

# 6. FITUR UTAMA
@app.post("/api/v1/import-csv", tags=["1. Import Data"], summary="Import Dataset Dinsos")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode('utf-8')))
    kolom_sah = [c.name for c in models.Keluarga.__table__.columns]
    
    kk_existing = {k[0] for k in db.query(models.Keluarga.nomor_kartu_keluarga).all()}
    
    sukses = 0
    objek_baru = []
    
    for row in reader:
        try:
            no_kk_row = row.get("nomor_kartu_keluarga")
            if not no_kk_row or no_kk_row in kk_existing:
                continue
            
            data_bersih = {}
            for k, v in row.items():
                if not k or k not in kolom_sah: continue
                val_str = str(v).strip().upper() if v else ""
                
                if k.startswith("kode_"): 
                    data_bersih[k] = val_str.replace(".", "")
                elif k.startswith("aset_") or k.startswith("pbi_") or k == "kepemilikan_aset":
                    data_bersih[k] = True if val_str in ["YA", "1", "TRUE"] else False
                elif k in ["skor", "desil_nasional"]:
                    try: data_bersih[k] = int(float(v)) if v else None
                    except ValueError: data_bersih[k] = None
                elif k.startswith("jumlah_") or k in ["luas_lantai", "daya_terpasang", "status_kepemilikan_rumah", "jenis_lantai_terluas", "jenis_dinding_terluas", "jenis_atap_terluas", "sumber_air_minum_utama", "sumber_penerangan_utama", "bahan_bakar_utama_memasak", "fasilitas_bab", "jenis_kloset", "pembuangan_akhir_tinja"]:
                    try: data_bersih[k] = int(float(v)) if v else 0
                    except ValueError: data_bersih[k] = 0
                else: 
                    data_bersih[k] = v
            
            objek_baru.append(models.Keluarga(**data_bersih))
            kk_existing.add(no_kk_row)
            sukses += 1
        except Exception as e: 
            print(f"Error baris: {e}")
            continue
    
    if objek_baru:
        db.add_all(objek_baru)
        db.commit()
        
    return {"status": "Sukses", "pesan": f"{sukses} data keluarga BARU berhasil ditambahkan (data duplikat diabaikan)."}

@app.post("/api/v1/asesmen/sosial", tags=["2. Asesmen Tim 1 & 3"], summary="Update Data & Hitung Desil 1 per 1")
async def asesmen_sosial(data: DataWarga, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.nomor_kartu_keluarga == data.nomor_kartu_keluarga).first()
    
    if keluarga:
        for key, value in data.model_dump().items():
            setattr(keluarga, key, value)
    else:
        keluarga = models.Keluarga(**data.model_dump())
        db.add(keluarga)
        
    db.commit()
    db.refresh(keluarga)
    
    try:
        async with httpx.AsyncClient() as client:
            res_tim1 = await client.post("http://127.0.0.1:8001/api/ai/tim1-klasifikasi", json=data.model_dump(), timeout=10.0)
            desil = res_tim1.json().get("desil", 0)
            
            payload_tim3 = data.model_dump()
            payload_tim3["desil"] = desil
            res_tim3 = await client.post("http://127.0.0.1:8001/api/ai/tim3-rekomendasi", json=payload_tim3, timeout=10.0)
            rekomendasi = str(res_tim3.json().get("rekomendasi", "Tidak ada"))
            
            hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()
            if not hitung:
                hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=current_user.id)
                db.add(hitung)
            
            hitung.desil_kemiskinan = str(desil)
            hitung.rekomendasi_bantuan = rekomendasi
            db.commit()
            
            return {"status": "Sukses", "no kk": keluarga.nomor_kartu_keluarga, "klasifikasi": res_tim1.json(), "rekomendasi": res_tim3.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/asesmen/visual/{no_kk}", tags=["3. Asesmen Tim 2"], summary="Upload 1 Foto Berdasarkan KK")
async def asesmen_visual(no_kk: str, file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Cari data warga berdasarkan no_kk
    keluarga = db.query(models.Keluarga).filter(models.Keluarga.nomor_kartu_keluarga == no_kk).first()
    if not keluarga:
        raise HTTPException(status_code=404, detail="Data dengan no kk tersebut belum ada di database! Masukkan via Asesmen Sosial dulu.")

    try:
        # 2. Upload 1 foto ke MinIO
        content = await file.read()
        nama_unik = f"{no_kk}_{file.filename}"
        s3_client.put_object(Bucket=MINIO_BUCKET, Key=nama_unik, Body=content, ContentType=file.content_type)
        url_foto = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{nama_unik}"

        # 3. Tembak Tim 2 (Analisis Visual)
        await file.seek(0)
        async with httpx.AsyncClient() as client:
            files_payload = {"file": (file.filename, file.file, file.content_type)}
            res_ai = await client.post("http://127.0.0.1:8001/api/ai/tim2-visual", files=files_payload, timeout=15.0)
            
            hasil_ai = res_ai.json()
            kondisi_teks = str(hasil_ai.get("reasoning", hasil_ai))

        # 4. Simpan ke database
        hitung = db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga.id).first()
        if not hitung:
            hitung = models.Perhitungan(keluarga_id=keluarga.id, user_id=current_user.id)
            db.add(hitung)

        # Masukkan variabel yang sudah berwujud teks dan URL
        hitung.kondisi_rumah = kondisi_teks
        hitung.foto_url = url_foto
        db.commit()

        return {"status": "Sukses", "url_foto": url_foto, "analisis_ai": hasil_ai}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))