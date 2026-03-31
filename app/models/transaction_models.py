
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class TransactionBase(BaseModel):
    from_account_id: str
    to_account_id: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(..., pattern=r"^(UAH|USD|EUR)$")
    type: str = Field(..., pattern=r"^(transfer|payment|income)$")
    category: str = Field(..., min_length=1, max_length=100)
    merchant_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)


class TransferCreate(BaseModel):
    to_account_id: str
    amount: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)


class TransactionCreate(TransactionBase):
    is_income: bool = False


class TransactionInDB(TransactionBase):
    id: Optional[str] = None
    status: str = "success"
    is_income: bool = False
    created_at: datetime


class TransactionResponse(TransactionBase):
    id: str
    status: str
    is_income: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedTransactions(BaseModel):
    items: List[TransactionResponse]
    total: int
    limit: int
    offset: int
    has_more: bool