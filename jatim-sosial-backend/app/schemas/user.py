from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr = Field(..., example="analis@dinsos.go.id")
    username: str = Field(..., example="analis_jatim")
    password: str = Field(..., example="password123")
    role: str = Field(default="ANALIS", example="ANALIS")

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: str
    is_active: bool
    dibuat_pada: datetime

    class Config:
        from_attributes = True

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    new_password: Optional[str] = None