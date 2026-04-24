"""Pydantic-схеми для сутності Банківський рахунок."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    """Базова схема рахунку."""

    user_id: str
    card_number: str = Field(..., pattern=r"^\d{4} \*\*\*\* \*\*\*\* \d{4}$")
    currency: str = Field(..., pattern=r"^(UAH|USD|EUR)$")
    balance: float = Field(..., ge=0)


class AccountCreate(AccountBase):
    """Схема для створення нового рахунку."""
    pass


class AccountUpdate(BaseModel):
    """Схема для оновлення рахунку."""

    status: Optional[str] = None
    balance: Optional[float] = Field(None, ge=0)


class AccountInDB(AccountBase):
    """Внутрішня схема рахунку з полями БД."""

    id: Optional[str] = None
    status: str = "active"
    created_at: datetime


class AccountResponse(AccountBase):
    """Схема відповіді з даними рахунку."""

    id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True