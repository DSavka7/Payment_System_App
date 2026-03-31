from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional

from app.core.security import validate_password_strength


class UserBase(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+380\d{9}$", examples=["+380991234567"])
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    role: str = Field(default="USER")


class UserCreate(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+380\d{9}$")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class UserUpdate(BaseModel):
    phone: Optional[str] = Field(None, pattern=r"^\+380\d{9}$")
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = None


class UserInDB(UserBase):
    id: Optional[str] = None
    password_hash: str
    status: str = "active"
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    phone: str
    first_name: str
    last_name: str
    role: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str