from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app import models
from app.security import get_current_user, get_password_hash, create_access_token
from app.schemas import user as user_schema

router = APIRouter(tags=["2. Manajemen User"])

# profile user yang sedang login
@router.get(
    "/api/v1/users/me",
    summary="Ambil profil akun yang sedang login",
    response_model=user_schema.UserResponse
)
def get_my_profile(
    current_user: models.User = Depends(get_current_user),
):
    return current_user

@router.put(
    "/api/v1/users/me",
    summary="Edit profil akun sendiri (username, email, password)",
    response_model=user_schema.UserResponse
)
def update_my_profile(
    payload: user_schema.UpdateProfileRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Cek konflik username
    if payload.username and payload.username != current_user.username:
        if db.query(models.User).filter(models.User.username == payload.username).first():
            raise HTTPException(status_code=409, detail=f"Username '{payload.username}' sudah digunakan.")
        current_user.username = payload.username

    # Cek konflik email
    if payload.email and payload.email != current_user.email:
        if db.query(models.User).filter(models.User.email == payload.email).first():
            raise HTTPException(status_code=409, detail=f"Email '{payload.email}' sudah terdaftar.")
        current_user.email = payload.email

    # Update password jika diberikan
    if payload.new_password:
        if len(payload.new_password) < 6:
            raise HTTPException(status_code=400, detail="Password baru minimal 6 karakter.")
        current_user.password_hash = get_password_hash(payload.new_password)

    db.commit()
    db.refresh(current_user)

    # Buat token baru jika username berubah
    new_token = None
    if payload.username and payload.username != current_user.username:
        new_token = create_access_token(data={"sub": current_user.username})

    return current_user

# Manajemen user (hanya untuk admin)
@router.get(
    "/api/v1/users",
    summary="Ambil daftar semua pengguna sistem (hanya admin)",
    response_model=List[user_schema.UserResponse]
)
def get_users(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    users = db.query(models.User).order_by(models.User.dibuat_pada.asc()).all()
    return users

@router.post(
    "/api/v1/users",
    summary="Buat pengguna baru (hanya admin)",
    response_model=user_schema.UserResponse,
    status_code=201
)
def create_user(
    payload: user_schema.UserCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa menambah pengguna baru.")

    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=409, detail=f"Username '{payload.username}' sudah digunakan.")

    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=409, detail=f"Email '{payload.email}' sudah terdaftar.")

    # Admin hanya boleh membuat akun ANALIS, bukan ADMIN lain
    if payload.role != "ANALIS":
        raise HTTPException(status_code=403, detail="Admin hanya bisa membuat akun dengan role ANALIS.")

    new_user = models.User(
        username=payload.username,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role="ANALIS",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.delete(
    "/api/v1/users/{user_id}",
    summary="Hapus pengguna dari sistem (hanya admin)"
)
def delete_user(
    user_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa menghapus pengguna.")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")

    # Tidak bisa menghapus akun sendiri
    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus akun Anda sendiri.")

    # Tidak bisa menghapus akun ADMIN lain
    if user.role == "ADMIN":
        raise HTTPException(status_code=403, detail="Tidak dapat menghapus akun dengan role ADMIN.")

    db.delete(user)
    db.commit()
    return {"status": "Sukses", "pesan": f"Pengguna '{user.username}' berhasil dihapus."}

@router.patch(
    "/api/v1/users/{user_id}",
    summary="Update status aktif atau role pengguna (hanya admin)",
    response_model=user_schema.UserResponse
)
def update_user(
    user_id: UUID,
    is_active: bool = None,
    role: str = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa mengubah data pengguna.")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")

    # Tidak boleh mengubah status diri sendiri via endpoint ini
    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Gunakan endpoint /api/v1/users/me untuk mengubah profil Anda sendiri.")

    if is_active is not None:
        user.is_active = is_active
    if role is not None:
        # Role hanya bisa diubah ke ANALIS, tidak ke ADMIN
        if role == "ADMIN":
            raise HTTPException(status_code=403, detail="Tidak dapat mengubah role pengguna menjadi ADMIN.")
        if role != "ANALIS":
            raise HTTPException(status_code=400, detail="Role hanya bisa diubah ke ANALIS.")
        user.role = role

    db.commit()
    db.refresh(user)
    return user