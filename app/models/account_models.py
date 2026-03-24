from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    user_id: str
    card_number: str = Field(..., pattern=r"^\d{4} \*\*\*\* \*\*\*\* \d{4}$")
    currency: str = Field(..., pattern=r"^(UAH|USD|EUR)$")
    balance: float = Field(..., ge=0)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    status: Optional[str] = None
    balance: Optional[float] = Field(None, ge=0)


class AccountInDB(AccountBase):
    id: Optional[str] = None
    status: str = "active"
    created_at: datetime


class AccountResponse(AccountBase):
    id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True