"""Pydantic-схеми для сутності Банківський рахунок."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    """Базова схема рахунку."""
    user_id: str
    currency: str = Field(..., pattern=r"^(UAH|USD|EUR)$")
    balance: float = Field(default=0.0, ge=0)


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
    card_number: str = ""
    card_number_full: Optional[str] = None
    status: str = "active"
    created_at: datetime


class AccountResponse(AccountBase):
    """Схема відповіді з даними рахунку."""
    id: str
    card_number: str
    card_number_full: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TransferRequest(BaseModel):
    """Схема запиту на переказ коштів."""
    from_account_id: str
    to_card_number: str = Field(..., min_length=16, max_length=16)
    amount: float = Field(..., gt=0)
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    """Спрощена схема відповіді після переказу."""
    id: str
    from_account_id: str
    to_account_id: str
    amount: float
    currency: str
    status: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True