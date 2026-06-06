from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, crud
from app.security import get_password_hash, verify_password, create_access_token, create_refresh_token
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
async def login(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username atau password salah.")
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # Set cookies HttpOnly
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=900,  # 15 menit
        expires=900,
        samesite="lax",
        secure=False  # Ubah ke True di HTTPS/production
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=604800,  # 7 hari
        expires=604800,
        samesite="lax",
        secure=False  # Ubah ke True di HTTPS/production
    )
    
    return {
        "username": user.username,
        "role": user.role
    }

@router.post("/refresh", summary="Segarkan token akses menggunakan refresh token")
async def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token tidak ditemukan.")
        
    try:
        from app.security import SECRET_KEY, ALGORITHM
        from jose import jwt, JWTError
        
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if token_type != "refresh" or username is None:
            raise HTTPException(status_code=401, detail="Refresh token tidak valid.")
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token tidak valid atau sudah kadaluarsa.")
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Pengguna tidak ditemukan.")
        
    new_access_token = create_access_token(data={"sub": user.username})
    new_refresh_token = create_refresh_token(data={"sub": user.username})
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        max_age=900,
        expires=900,
        samesite="lax",
        secure=False
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        max_age=604800,
        expires=604800,
        samesite="lax",
        secure=False
    )
    
    return {
        "username": user.username,
        "role": user.role
    }

@router.post("/logout", summary="Logout dan hapus cookie token")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"status": "Sukses", "pesan": "Logout berhasil"}