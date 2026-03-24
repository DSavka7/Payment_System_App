from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RequestBase(BaseModel):
    user_id: str
    account_id: str
    type: str = Field(..., pattern=r"^(BLOCK|UNBLOCK|LIMIT_CHANGE)$")
    message: str


class RequestCreate(RequestBase):
    pass


class RequestUpdate(BaseModel):
    status: str
    admin_comment: Optional[str] = None


class RequestInDB(RequestBase):
    id: Optional[str] = None
    status: str = "pending"
    admin_comment: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class RequestResponse(RequestBase):
    id: str
    status: str
    admin_comment: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True