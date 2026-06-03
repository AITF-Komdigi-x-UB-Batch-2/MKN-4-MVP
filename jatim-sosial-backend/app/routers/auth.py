from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, crud
from app.security import get_password_hash, verify_password, create_access_token
from app.schemas import user as user_schema

router = APIRouter(tags=["1. Auth"])

@router.post("/register", summary="Registrasi user baru (publik, untuk kebutuhan dev/debug saja)")
def register(payload: user_schema.UserCreate, db: Session = Depends(get_db)):

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
        password_hash=get_password_hash(payload.password),
        role=payload.role
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

@router.post("/login", summary="Login dan dapatkan token JWT")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username atau password salah.")
    
    token = create_access_token(data={"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role
    }