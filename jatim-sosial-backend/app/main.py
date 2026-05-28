import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, ensure_nik_columns, SessionLocal
from app.security import get_password_hash
from app import models
from sqlalchemy import text

# 1. Jalankan migrasi kolom NIK dan pembuatan tabel database otomatis
models.Base.metadata.create_all(bind=engine)
ensure_nik_columns()

# 2. Inisialisasi Aplikasi FastAPI
app = FastAPI(
    title="API Pemetaan Kemiskinan Jatim",
    version="2.1",
    description="Backend MVP Tim 4 — Mengorkestrasi alur data dari Tim 1, 2, dan 3 (Versi Modular)."
)

# 3. Setup CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    print("Menjalankan Main Server di Port 8000...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)