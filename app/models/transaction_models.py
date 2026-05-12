"""Pydantic-схеми для сутності Транзакція."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


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
    is_suspicious: bool = False


class TransactionInDB(TransactionBase):
    """Внутрішня схема транзакції з полями БД."""

    id: Optional[str] = None
    # Можливі статуси: success | pending_review | approved | rejected
    status: str = "success"
    is_income: bool = False
    is_suspicious: bool = False
    review_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    created_at: datetime


class TransactionResponse(TransactionBase):
    """Схема відповіді з даними транзакції."""

    id: str
    status: str
    is_income: bool
    is_suspicious: bool = False
    review_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionReviewUpdate(BaseModel):
    """
    Схема для перевірки підозрілої транзакції адміністратором.
    Адмін може схвалити або відхилити транзакцію.
    """

    action: str = Field(
        ...,
        pattern=r"^(approve|reject)$",
        description="approve — схвалити переказ, reject — відхилити та повернути кошти",
    )
    comment: Optional[str] = Field(
        None,
        max_length=500,
        description="Коментар адміністратора (необов'язково)",
    )


class TransactionListResponse(BaseModel):
    """Схема відповіді зі списком транзакцій та пагінацією."""

    items: list
    total: int
    limit: int
    offset: int

    class Config:
        from_attributes = True


class SuspiciousTransactionResponse(TransactionBase):
    """
    Розширена схема підозрілої транзакції для адмін-панелі.
    Містить додаткову інформацію для прийняття рішення.
    """

    id: str
    status: str
    is_suspicious: bool
    is_income: bool
    review_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True