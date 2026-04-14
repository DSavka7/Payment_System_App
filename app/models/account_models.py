from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    user_id: str
    currency: str = Field(..., pattern=r"^(UAH|USD|EUR)$", examples=["UAH"])
    balance: float = Field(0.0, ge=0, examples=[1000.0])


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    status: Optional[str] = None
    balance: Optional[float] = Field(None, ge=0)


class AccountInDB(BaseModel):
    id: Optional[str] = None
    user_id: str
    card_number_full: str
    currency: str
    balance: float
    status: str = "active"
    created_at: datetime

    @property
    def card_number(self) -> str:
        n = self.card_number_full
        return f"{n[:4]} **** **** {n[-4:]}"


class AccountResponse(BaseModel):
    id: str
    user_id: str
    card_number: str
    card_number_full: str
    currency: str
    balance: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TransferRequest(BaseModel):
    from_account_id: str
    to_card_number: str = Field(..., pattern=r"^\d{16}$")
    amount: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=255)