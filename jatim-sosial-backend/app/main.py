"""
FILE: app/main.py
DESKRIPSI:
Main application entry point FastAPI. Menginisialisasi server, setup CORS,
menjalankan migrasi skema database otomatis (termasuk kolom NIK),
memastikan bucket MinIO ada, dan mendaftarkan semua router API (Auth, Users, Items, Asesmen).
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, SessionLocal
from app.security import get_password_hash
from app import models
from sqlalchemy import text
from app.config import APP_HOST, APP_PORT, ensure_bucket_exists
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app_service.log"), # Menyimpan log ke file
        logging.StreamHandler()                 # Tetap menampilkan di terminal
    ]
)

# Cara pakai di dalam endpoint atau fungsi:
# logging.info("Proses sinkronisasi CSV dimulai.")
# logging.error("Gagal terhubung ke server Tim 2.")

# 1. Inisialisasi Aplikasi FastAPI
app = FastAPI(
    title="API Pemetaan Kemiskinan Jatim",
    version="2.1",
    description="Backend MVP Tim 4 — Mengorkestrasi alur data dari Tim 1, 2, dan 3 (Versi Modular)."
)

# 2. Setup CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Init database & storage saat startup
@app.on_event("startup")
def init_app():
    models.Base.metadata.create_all(bind=engine)
    ensure_bucket_exists()

# 4. Seeder Akun Admin Otomatis saat Aplikasi Menyala
@app.on_event("startup")
def seed_admin_user():
    db = SessionLocal()
    try:
        db.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT \'ANALIS\';'))
        db.commit()

        admin = db.query(models.User).filter_by(username="admin_jatim").first()
        if not admin:
            admin = models.User(
                email="admin@dinsos.go.id",
                username="admin_jatim",
                password_hash=get_password_hash("admin123"),
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("[Seeder] Akun admin_jatim berhasil dibuat.")
        else:
            if admin.role != "ADMIN":
                admin.role = "ADMIN"
                db.commit()
            print("[Seeder] Akun admin_jatim sudah tersedia.")
    except Exception as e:
        print(f"[Seeder] Error seeding admin: {e}")
    finally:
        db.close()

# Cleanup Stuck Processes
@app.on_event("startup")
def cleanup_stuck_processes():
    db = SessionLocal()
    try:
        stuck_records = db.query(models.Perhitungan).filter(models.Perhitungan.status_validasi == "proses").all()
        if stuck_records:
            print(f"[Cleanup] Menemukan {len(stuck_records)} data dalam status 'proses'. Mereset status ke 'analisis'...")
            for record in stuck_records:
                record.status_validasi = "analisis"
            db.commit()
            print("[Cleanup] Reset status 'proses' berhasil.")
    except Exception as e:
        print(f"[Cleanup] Gagal membersihkan status 'proses': {e}")
    finally:
        db.close()

# 5. Rute Dasar untuk Testing Kesehatan API
@app.get("/")
def root():
    return {
        "status": "Online",
        "message": "Selamat datang di API Pemetaan Kemiskinan Jatim Versi Modular!"
    }

# 6. REGISTRASI JALUR API (ROUTER)
from app.routers import auth, users, items, asesmen

app.include_router(auth.router, prefix="/api/v1/auth", tags=["1. Auth"])
app.include_router(users.router) 
app.include_router(items.router) 
app.include_router(asesmen.router) 

if __name__ == "__main__":
    print(f"Menjalankan Main Server di Port {APP_PORT}...")
    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=True)