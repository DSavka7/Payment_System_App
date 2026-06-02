"""
Pydantic-схеми для сутності Користувач.
"""
import re
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional


def validate_password_strength(password: str) -> str:
    """Перевіряє надійність пароля за розширеними критеріями."""
    errors = []
    if len(password) < 8:
        errors.append("мінімум 8 символів")
    if not re.search(r"[A-Z]", password):
        errors.append("принаймні одна велика літера (A-Z)")
    if not re.search(r"[a-z]", password):
        errors.append("принаймні одна мала літера (a-z)")
    if not re.search(r"\d", password):
        errors.append("принаймні одна цифра (0-9)")
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]", password):
        errors.append("принаймні один спеціальний символ (!@#$%^&*...)")
    if errors:
        raise ValueError(f"Пароль не відповідає вимогам: {', '.join(errors)}")
    return password


class UserBase(BaseModel):
    """Базова схема користувача."""

    email: EmailStr
    phone: str = Field(..., pattern=r"^\+380\d{9}$")
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    role: str = Field(default="USER")


class UserCreate(UserBase):
    """Схема для створення нового користувача."""

    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[A-Za-zА-ЯҐЄІЇа-яґєії'\-\s]+$", v):
            raise ValueError("Ім'я може містити лише літери, апостроф та дефіс")
        return v.strip()


class UserUpdate(BaseModel):
    """Схема для оновлення даних користувача."""

    phone: Optional[str] = Field(None, pattern=r"^\+380\d{9}$")
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    status: Optional[str] = None

    # Зміна пароля
    current_password: Optional[str] = Field(None, description="Поточний пароль для підтвердження")
    password: Optional[str] = Field(None, min_length=8, description="Новий пароль")

    # Внутрішнє поле — встановлюється сервісом після хешування
    password_hash: Optional[str] = Field(None, exclude=True)

    @field_validator("password")
    @classmethod
    def check_new_password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_password_strength(v)


class UserInDB(UserBase):
    """Внутрішня схема користувача з даними з бази даних."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: Optional[str] = None
    password_hash: str
    status: str = "active"
    created_at: datetime
    # Причина блокування (встановлюється адміністратором)
    block_reason: Optional[str] = None


class UserResponse(UserBase):
    """Схема відповіді з даними користувача (без пароля)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    created_at: datetime
    block_reason: Optional[str] = None


class BlockedUserInfo(BaseModel):
    """
    Мінімальна схема для заблокованого користувача.
    Повертається замість повного профілю коли юзер заблокований.
    """

    id: str
    email: str
    status: str
    block_reason: Optional[str] = None
    message: str = "Ваш обліковий запис заблоковано. Зверніться до адміністратора."