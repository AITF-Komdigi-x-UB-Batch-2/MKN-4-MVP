"""
 * FILE: app/crud.py
 * DESKRIPSI:
 * Centralized Database Operations (CRUD) untuk entitas Users, Keluarga, dan Perhitungan.
 * Menangani logic bisnis dasar seperti hashing password, pengecekan duplikasi KK,
 * dan pengambilan relasi (foto, riwayat). 
 * 
 * CATATAN: Dibuat setelah kolom nik ditambahkan ke model Keluarga.
"""

from sqlalchemy.orm import Session
from uuid import UUID
from app import models
from app.security import get_password_hash

# ==========================================
# CRUD UNTUK USERS (PENGGUNA SISTEM)
# ==========================================

def get_user_by_username(db: Session, username: str):
    """Mencari user berdasarkan username"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """Mencari user berdasarkan email"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: UUID):
    """Mencari user berdasarkan ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, username: str, email: str, password_plain: str, role: str = "ANALIS"):
    """Memasukkan user baru ke database"""
    hashed_password = get_password_hash(password_plain)
    db_user = models.User(
        username=username,
        email=email,
        password_hash=hashed_password,
        role=role,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ==========================================
# CRUD UNTUK KELUARGA & ASESMEN
# ==========================================

def get_keluarga_by_id(db: Session, keluarga_id: UUID):
    """Mengambil data satu keluarga berdasarkan ID-nya"""
    return db.query(models.Keluarga).filter(models.Keluarga.id == keluarga_id).first()

def get_keluarga_by_kk(db: Session, nomor_kk: str):
    """Mengecek apakah Nomor KK sudah ada di sistem (Idempotensi)"""
    return db.query(models.Keluarga).filter(models.Keluarga.nomor_kartu_keluarga == nomor_kk).first()

def get_perhitungan_by_keluarga(db: Session, keluarga_id: UUID):
    """Mencari data perhitungan AI untuk keluarga tertentu"""
    return db.query(models.Perhitungan).filter(models.Perhitungan.keluarga_id == keluarga_id).first()

def get_foto_utama_keluarga(db: Session, keluarga_id: UUID):
    """Mengambil foto tampak luar terbaru dari keluarga"""
    return db.query(models.Foto).filter(
        models.Foto.keluarga_id == keluarga_id,
        models.Foto.tampak_dalam == False
    ).order_by(models.Foto.diunggah_pada.desc()).first()