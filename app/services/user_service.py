"""
Сервісний шар для управління користувачами.
"""
from typing import Dict, Optional
from fastapi import Depends
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import InvalidCredentials, UserNotFound
from app.core.logging_config import get_logger
from app.core.security import verify_password, create_access_token
from app.db.database import get_db
from app.models.user_models import UserCreate, UserResponse, UserUpdate
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserService:
    """Сервіс для управління користувачами."""

    def __init__(self, repo: UserRepository, db: Optional[AsyncIOMotorDatabase] = None):
        self.repo = repo
        self._db = db

    async def create_user(self, user: UserCreate) -> UserResponse:
        """Реєструє нового користувача."""
        user_in_db = await self.repo.create(user)
        logger.info("Зареєстровано: email=%s id=%s", user.email, user_in_db.id)
        return UserResponse.model_validate(user_in_db)

    async def authenticate(self, email: str, password: str) -> Dict:
        """
        Автентифікує користувача.
        Заблокований може увійти — але /users/me поверне 403.
        """
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            logger.warning("Невдала спроба входу: email=%s", email)
            raise InvalidCredentials()

        token = create_access_token({"sub": user.id, "role": user.role})
        logger.info("Вхід: id=%s, status=%s", user.id, user.status)
        return {"access_token": token, "token_type": "bearer"}

    async def get_me(self, user_id: str):
        """
        Повертає профіль поточного юзера.
        Якщо заблокований — JSONResponse 403 з причиною.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFound()

        if user.status == "blocked":
            return JSONResponse(
                status_code=403,
                content={
                    "blocked": True,
                    "id": user.id,
                    "email": user.email,
                    "status": "blocked",
                    "block_reason": user.block_reason or "Причину не вказано",
                    "message": "Ваш обліковий запис заблоковано адміністратором.",
                    "detail": "Обліковий запис заблоковано",
                },
            )

        return UserResponse.model_validate(user)

    async def get_user(self, user_id: str) -> UserResponse:
        """Повертає дані користувача за ID."""
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: str, update_data: UserUpdate) -> UserResponse:
        """Оновлює профіль."""
        user = await self.repo.update(user_id, update_data)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user)

    async def refresh(self, refresh_token: str) -> Dict:
        """
        Оновлює access token.
        ВАЖЛИВО: використовує `is not None` — Motor DB не підтримує bool().
        """
        if self._db is None:
            raise InvalidCredentials()

        doc = await self._db.refresh_tokens.find_one({"token": refresh_token})
        if not doc:
            raise InvalidCredentials()

        user = await self.repo.get_by_id(str(doc["user_id"]))
        if not user:
            raise InvalidCredentials()

        token = create_access_token({"sub": user.id, "role": user.role})
        return {"access_token": token, "token_type": "bearer"}

    async def logout(self, refresh_token: str) -> None:
        """Видаляє refresh token."""
        if self._db is not None:
            await self._db.refresh_tokens.delete_one({"token": refresh_token})


def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db.users)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserService:
    return UserService(repo, db)