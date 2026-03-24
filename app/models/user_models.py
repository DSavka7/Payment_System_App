from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+380\d{9}$")
    role: str = Field(default="USER")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    phone: Optional[str] = None
    status: Optional[str] = None


class UserInDB(UserBase):
    id: Optional[str] = None
    password_hash: str
    status: str = "active"
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True   # важливо для alias="_id"


class UserResponse(UserBase):
    id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True