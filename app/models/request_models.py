"""Pydantic-схеми для сутності Запит (на блокування/розблокування рахунку)."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RequestBase(BaseModel):
    """Базова схема запиту."""

    user_id: str
    account_id: str
    type: str = Field(..., pattern=r"^(BLOCK|UNBLOCK|LIMIT_CHANGE)$")
    message: str


class RequestCreate(RequestBase):
    """Схема для створення нового запиту."""
    pass


class RequestUpdate(BaseModel):
    """Схема для оновлення статусу запиту адміністратором."""

    status: str
    admin_comment: Optional[str] = None


class RequestInDB(RequestBase):
    """Внутрішня схема запиту з полями БД."""

    id: Optional[str] = None
    status: str = "pending"
    admin_comment: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class RequestResponse(RequestBase):
    """Схема відповіді з даними запиту."""

    id: str
    status: str
    admin_comment: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True