"""Pydantic-схеми для сутності Користувач (User)."""
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Базові поля користувача."""
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+380\d{9}$", examples=["+380991234567"])
    role: str = Field(default="USER")


class UserCreate(UserBase):
    """Схема для реєстрації нового користувача."""
    password: str = Field(..., min_length=8, examples=["SecurePass1"])


class UserUpdate(BaseModel):
    """Схема для часткового оновлення даних користувача."""
    phone: Optional[str] = Field(None, pattern=r"^\+380\d{9}$")
    status: Optional[str] = None


class UserInDB(UserBase):
    """Внутрішнє представлення користувача (з хешем паролю)."""
    id: Optional[str] = None
    password_hash: str
    status: str = "active"
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class UserResponse(UserBase):
    """Публічне представлення користувача (без пароля)."""
    id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Відповідь при успішній автентифікації."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Запит на оновлення access token."""
    refresh_token: str