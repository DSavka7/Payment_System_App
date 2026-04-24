"""
Pydantic-схеми для сутності Користувач.
Містить моделі для створення, оновлення та відображення користувачів.
"""
import re
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional


def validate_password_strength(password: str) -> str:
    """
    Перевіряє надійність пароля за розширеними критеріями.

    Вимоги:
    - Мінімум 8 символів
    - Принаймні одна велика літера
    - Принаймні одна мала літера
    - Принаймні одна цифра
    - Принаймні один спеціальний символ (!@#$%^&*()_+-=[]{}|;:,.<>?)
    """
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
    """Базова схема користувача з обов'язковими полями."""

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
        """Перевіряє складність пароля."""
        return validate_password_strength(v)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Перевіряє, що ім'я/прізвище містить лише літери та дефіс."""
        if not re.match(r"^[A-Za-zА-ЯҐЄІЇа-яґєії'\-\s]+$", v):
            raise ValueError("Ім'я може містити лише літери, апостроф та дефіс")
        return v.strip()


class UserUpdate(BaseModel):
    """Схема для оновлення даних користувача."""

    phone: Optional[str] = Field(None, pattern=r"^\+380\d{9}$")
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    status: Optional[str] = None


class UserInDB(UserBase):
    """Внутрішня схема користувача з даними з бази даних."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: Optional[str] = None
    password_hash: str
    status: str = "active"
    created_at: datetime


class UserResponse(UserBase):
    """Схема відповіді з даними користувача (без пароля)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    created_at: datetime