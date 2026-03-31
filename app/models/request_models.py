

from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional, List


class RequestBase(BaseModel):
    """Базові поля запиту."""
    user_id: str
    account_id: str
    type: str = Field(..., pattern=r"^(UNBLOCK|LIMIT_CHANGE)$")
    message: str = Field(..., min_length=10, max_length=1000)


class RequestCreate(BaseModel):

    account_id: str
    type: str = Field(
        ...,
        pattern=r"^(UNBLOCK|LIMIT_CHANGE)$",
        description="UNBLOCK — розблокування рахунку, LIMIT_CHANGE — зміна ліміту",
    )
    message: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Причина/пояснення запиту",
    )
    requested_limit: Optional[float] = Field(
        None,
        gt=0,
        description="Новий добовий ліміт (обов'язково для LIMIT_CHANGE)",
    )

    @model_validator(mode="after")
    def validate_limit_for_limit_change(self) -> "RequestCreate":

        if self.type == "LIMIT_CHANGE" and self.requested_limit is None:
            raise ValueError(
                "Поле requested_limit є обов'язковим для запиту типу LIMIT_CHANGE"
            )
        return self


class RequestUpdate(BaseModel):
    """Схема для оновлення статусу запиту адміністратором."""
    status: str = Field(..., pattern=r"^(approved|rejected)$")
    admin_comment: Optional[str] = Field(None, max_length=500)


class RequestInDB(RequestBase):
    """Внутрішня схема запиту."""
    id: Optional[str] = None
    status: str = "pending"
    admin_comment: Optional[str] = None
    requested_limit: Optional[float] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class RequestResponse(RequestBase):
    """Публічна схема відповіді запиту."""
    id: str
    status: str
    admin_comment: Optional[str] = None
    requested_limit: Optional[float] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedRequests(BaseModel):
    """Пагінована відповідь зі списком запитів."""
    items: List[RequestResponse]
    total: int
    limit: int
    offset: int
    has_more: bool