"""Pydantic-схеми для сутності Банківський рахунок."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    """Базова схема рахунку."""
    user_id: str
    currency: str = Field(..., pattern=r"^(UAH|USD|EUR)$")
    balance: float = Field(..., ge=0)


class AccountCreate(AccountBase):
    card_number: Optional[str] = None
    card_number_full: Optional[str] = None


class AccountUpdate(BaseModel):
    """Схема для оновлення рахунку."""
    status: Optional[str] = None
    balance: Optional[float] = Field(None, ge=0)
    block_reason: Optional[str] = None


class AccountInDB(AccountBase):
    """Внутрішня схема рахунку з полями БД."""
    id: Optional[str] = None
    card_number: str = ""
    card_number_full: Optional[str] = None
    status: str = "active"
    created_at: datetime
    block_reason: Optional[str] = None


class AccountResponse(AccountBase):
    """Схема відповіді — card_number_full повертається для копіювання на фронті."""
    id: str
    card_number: str
    card_number_full: Optional[str] = None
    status: str
    created_at: datetime
    block_reason: Optional[str] = None

    class Config:
        from_attributes = True


class TransferRequest(BaseModel):
    """Схема запиту на переказ коштів."""
    from_account_id: str = Field(..., description="ID рахунку відправника")
    to_account_id: Optional[str] = Field(None)
    to_card_number: Optional[str] = Field(None, pattern=r"^\d{16}$")
    amount: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=255)


class TransferResponse(BaseModel):
    """Схема відповіді після переказу."""
    id: str
    from_account_id: str
    to_account_id: Optional[str]
    amount: float
    currency: str
    status: str
    is_suspicious: bool = False
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True