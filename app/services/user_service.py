from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict

from app.repositories.user_repository import UserRepository
from app.models.user_models import UserCreate, UserResponse, UserUpdate
from app.core.security import verify_password, create_access_token
from app.core.exceptions import UserNotFound, InvalidCredentials
from app.db.database import get_db   # ← тепер імпорт працює


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, user: UserCreate) -> UserResponse:
        user_in_db = await self.repo.create(user)
        return UserResponse.model_validate(user_in_db)

    async def authenticate(self, email: str, password: str) -> Dict:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentials()

        token = create_access_token({"sub": user.id, "role": user.role})
        return {"access_token": token, "token_type": "bearer"}

    async def get_user(self, user_id: str) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user)


# Dependency Injection
def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    return UserRepository(db.users)


def get_user_service(repo: UserRepository = Depends(get_user_repository)):
    return UserService(repo)