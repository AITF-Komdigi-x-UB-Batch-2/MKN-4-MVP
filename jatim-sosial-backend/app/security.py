"""
FILE: app/security.py
DESKRIPSI:
Manajemen Keamanan Aplikasi: Hashing Password (bcrypt), Validasi Token JWT,
 dan Dependency Injection untuk autentikasi pengguna (get_current_user).
"""

import os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Import dari dalam folder app
from app.database import get_db
from app import models

load_dotenv()

# --- KONFIGURASI JWT ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

import bcrypt

pwd_context = None
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"[DEBUG] verify_password error: {e}")
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- DEPENDENCY: PENJAGA PINTU ---
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> models.User:    
    # 1. Cek dari HttpOnly Cookies
    token = request.cookies.get("access_token")
    
    # 2. Fallback ke Authorization Header (untuk Swagger / Dev)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(status_code=401, detail="Token tidak ditemukan.")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        
        if token_type != "access":
            raise HTTPException(status_code=401, detail="Token akses tidak valid.")
            
        if username is None:
            raise HTTPException(status_code=401, detail="Token tidak memiliki identitas pengguna.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kadaluarsa.")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Pengguna tidak ditemukan.")
    return user