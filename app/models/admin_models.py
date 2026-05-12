"""Pydantic-схеми для адміністративних операцій."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class AdminUserResponse(BaseModel):
    id: str
    email: str
    phone: str
    first_name: str
    last_name: str
    role: str
    status: str
    created_at: datetime
    accounts_count: int = 0
    block_reason: Optional[str] = None

    class Config:
        from_attributes = True


class AdminAccountInfo(BaseModel):
    id: str
    card_number: str
    currency: str
    balance: float
    status: str
    created_at: datetime
    block_reason: Optional[str] = None   # ← причина блокування рахунку


class AdminTransactionInfo(BaseModel):
    id: str
    from_account_id: str
    to_account_id: Optional[str]
    amount: float
    currency: str
    type: str
    status: str
    is_suspicious: bool
    description: Optional[str]
    created_at: datetime


class AdminUserDetailsResponse(BaseModel):
    id: str
    email: str
    phone: str
    first_name: str
    last_name: str
    role: str
    status: str
    created_at: datetime
    block_reason: Optional[str] = None
    accounts: List[AdminAccountInfo] = []
    recent_transactions: List[AdminTransactionInfo] = []
    total_transactions: int = 0
    total_balance_uah: float = 0.0


class AdminUserStatusUpdate(BaseModel):
    """Блокування/розблокування користувача. Причина обов'язкова."""
    status: str = Field(..., pattern=r"^(active|blocked)$")
    reason: str = Field(..., min_length=5, max_length=500,
                        description="Обов'язково, мін. 5 символів")


class AdminAccountStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(active|blocked)$")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Необов'язково. Буде показана власнику рахунку.",
    )


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    blocked_users: int
    total_accounts: int
    total_transactions: int
    pending_requests: int
    suspicious_transactions: int
    pending_review_transactions: int


class AdminUserListResponse(BaseModel):
    items: List[AdminUserResponse]
    total: int
    limit: int
    offset: int