"""Pydantic-схеми для сутності Транзакція."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class TransactionBase(BaseModel):
    """Базова схема транзакції."""
    from_account_id: str
    to_account_id: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(..., pattern=r"^(UAH|USD|EUR)$")
    type: str = Field(..., pattern=r"^(transfer|payment|income)$")
    category: str
    merchant_name: Optional[str] = None
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Схема для створення транзакції."""
    is_income: bool = False


class TransactionInDB(TransactionBase):
    """Внутрішня схема транзакції з полями БД."""
    id: Optional[str] = None
    status: str = "success"
    is_income: bool = False
    created_at: datetime


class TransactionResponse(TransactionBase):
    """Схема відповіді з даними транзакції."""
    id: str
    status: str
    is_income: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Відповідь зі списком транзакцій та загальною кількістю (для пагінації)."""
    items: List[TransactionResponse]
    total: int