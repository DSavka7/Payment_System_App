
from datetime import datetime, timezone
from typing import Dict

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import InvalidCredentials, InvalidToken, UserNotFound
from app.core.logging_config import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.database import get_db
from app.models.user_models import (
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserService:

    def __init__(self, repo: UserRepository, db: AsyncIOMotorDatabase) -> None:
        self.repo = repo
        self.db = db

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def create_user(self, user: UserCreate) -> UserResponse:
        user_in_db = await self.repo.create(user)
        logger.info("Новий користувач зареєстрований: %s", user.email)
        return UserResponse.model_validate(user_in_db.model_dump())

    async def authenticate(self, email: str, password: str) -> TokenResponse:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            logger.warning("Невдала спроба входу для email: %s", email)
            raise InvalidCredentials()

        payload = {"sub": user.id, "role": user.role}
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        await self.db.refresh_tokens.insert_one({
            "user_id": user.id,
            "token": refresh_token,
            "created_at": datetime.now(timezone.utc),
        })

        logger.info("Користувач увійшов: %s", email)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_access_token(self, request: RefreshRequest) -> TokenResponse:
        payload = decode_token(request.refresh_token)

        if payload.get("type") != "refresh":
            raise InvalidToken()

        stored = await self.db.refresh_tokens.find_one(
            {"token": request.refresh_token}
        )
        if not stored:
            logger.warning("Спроба використати невідомий refresh token")
            raise InvalidToken()

        user_id = payload.get("sub")
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise InvalidToken()

        new_access = create_access_token({"sub": user.id, "role": user.role})
        logger.info("Access token оновлено для user_id: %s", user_id)
        return TokenResponse(
            access_token=new_access,
            refresh_token=request.refresh_token,
        )

    async def logout(self, refresh_token: str) -> None:
        await self.db.refresh_tokens.delete_one({"token": refresh_token})
        logger.info("Refresh token відкликано")

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def get_user(self, user_id: str) -> UserResponse:
        """Повертає публічні дані користувача за ID."""
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user.model_dump())

    async def update_user(self, user_id: str, update_data: UserUpdate) -> UserResponse:
        """Оновлює дані користувача."""
        user = await self.repo.update(user_id, update_data)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user.model_dump())

    async def delete_user(self, user_id: str) -> Dict:
        deleted = await self.repo.delete(user_id)
        if not deleted:
            raise UserNotFound()
        logger.info("Користувача видалено: %s", user_id)
        return {"detail": "Користувача видалено / User deleted"}


# ── Dependency Injection ───────────────────────────────────────────────────────

def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db.users)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserService:
    return UserService(repo, db)