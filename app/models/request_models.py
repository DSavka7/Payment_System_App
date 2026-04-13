from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RequestBase(BaseModel):
    """Базові поля запиту користувача до адміністратора."""
    user_id: str
    account_id: str
    type: str = Field(..., pattern=r"^(BLOCK|UNBLOCK|LIMIT_CHANGE)$")
    message: str = Field(..., max_length=1000)


class RequestCreate(RequestBase):
    """Схема для створення нового запиту."""
    pass


class RequestUpdate(BaseModel):
    """Схема для оновлення статусу запиту адміністратором."""
    status: str = Field(..., pattern=r"^(approved|rejected|pending)$")
    admin_comment: Optional[str] = Field(None, max_length=500)


class RequestInDB(RequestBase):
    """Внутрішнє представлення запиту."""
    id: Optional[str] = None
    status: str = "pending"
    admin_comment: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class RequestResponse(RequestBase):
    """Публічне представлення запиту."""
    id: str
    status: str
    admin_comment: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True