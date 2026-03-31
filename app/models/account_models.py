
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    user_id: str
    card_number: str = Field(
        ...,
        pattern=r"^\d{4} \*\*\*\* \*\*\*\* \d{4}$",
        examples=["5375 **** **** 1234"],
    )
    currency: str = Field(..., pattern=r"^(UAH|USD|EUR)$")
    balance: float = Field(..., ge=0)


class AccountCreate(BaseModel):
    card_number: str = Field(..., pattern=r"^\d{4} \*\*\*\* \*\*\*\* \d{4}$")
    currency: str = Field(..., pattern=r"^(UAH|USD|EUR)$")
    balance: float = Field(default=0.0, ge=0)
    daily_limit: Optional[float] = Field(default=None, gt=0)


class AccountUpdate(BaseModel):
    status: Optional[str] = None
    balance: Optional[float] = Field(None, ge=0)
    daily_limit: Optional[float] = Field(None, gt=0)


class AccountInDB(AccountBase):
    id: Optional[str] = None
    status: str = "active"
    daily_limit: Optional[float] = None
    created_at: datetime


class AccountResponse(AccountBase):
    id: str
    status: str
    daily_limit: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True