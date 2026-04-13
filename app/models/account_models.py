from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    """Базові поля банківського рахунку."""
    user_id: str
    card_number: str = Field(
        ...,
        pattern=r"^\d{4} \*\*\*\* \*\*\*\* \d{4}$",
        examples=["1234 **** **** 5678"],
    )
    currency: str = Field(..., pattern=r"^(UAH|USD|EUR)$", examples=["UAH"])
    balance: float = Field(..., ge=0, examples=[1000.0])


class AccountCreate(AccountBase):
    """Схема для створення нового рахунку."""
    pass


class AccountUpdate(BaseModel):
    """Схема для оновлення рахунку (статус або баланс)."""
    status: Optional[str] = None
    balance: Optional[float] = Field(None, ge=0)


class AccountInDB(AccountBase):
    """Внутрішнє представлення рахунку."""
    id: Optional[str] = None
    status: str = "active"
    created_at: datetime


class AccountResponse(AccountBase):
    """Публічне представлення рахунку."""
    id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TransferRequest(BaseModel):
    """Схема запиту на переказ між рахунками."""
    from_account_id: str = Field(..., description="ID рахунку-відправника")
    to_account_id: str = Field(..., description="ID рахунку-отримувача")
    amount: float = Field(..., gt=0, description="Сума переказу")
    description: Optional[str] = Field(None, max_length=255)