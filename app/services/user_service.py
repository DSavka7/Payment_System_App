import datetime
from typing import Dict, Optional

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import (
    InvalidCredentials, UserNotFound, UserInactive, TokenExpired,
    WrongCurrentPassword,
)
from app.core.logging_config import get_logger
from app.core.security import verify_password, create_access_token, decode_access_token
from app.db.database import get_db
from app.models.user_models import UserCreate, UserResponse, UserUpdate
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserService:

    def __init__(self, repo: UserRepository, db: AsyncIOMotorDatabase):
        self.repo = repo
        self.db = db

    async def create_user(self, user: UserCreate) -> UserResponse:
        user_in_db = await self.repo.create(user)
        logger.info("Registered: email=%s id=%s", user.email, user_in_db.id)
        return UserResponse.model_validate(user_in_db)

    async def authenticate(self, email: str, password: str) -> Dict:
        """Authenticate user and return access + refresh tokens."""
        user = await self.repo.get_by_email(email)
        success = bool(user and verify_password(password, user.password_hash))

        if not success:
            logger.warning("Failed login attempt: email=%s", email)
            raise InvalidCredentials()

        if user.status != "active":
            logger.warning("Blocked account login attempt: id=%s", user.id)
            raise UserInactive()

        access_token = create_access_token({"sub": user.id, "role": user.role})
        refresh_token = create_access_token(
            {"sub": user.id, "role": user.role, "type": "refresh"},
            expires_delta=datetime.timedelta(days=7),
        )

        await self.db.refresh_tokens.insert_one({
            "token": refresh_token,
            "user_id": user.id,
            "created_at": datetime.datetime.utcnow(),
        })

        logger.info("Успішний вхід: id=%s", user.id)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def refresh(self, refresh_token: str) -> Dict:
        """Issue new access token using a valid refresh token."""
        payload = decode_access_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise TokenExpired()

        doc = await self.db.refresh_tokens.find_one({"token": refresh_token})
        if not doc:
            raise TokenExpired()

        user = await self.repo.get_by_id(payload.get("sub", ""))
        if not user or user.status != "active":
            raise TokenExpired()

        new_access = create_access_token({"sub": user.id, "role": user.role})
        return {"access_token": new_access, "token_type": "bearer"}

    async def logout(self, refresh_token: str) -> None:
        """Invalidate refresh token."""
        await self.db.refresh_tokens.delete_one({"token": refresh_token})
        logger.info("Logout: refresh token invalidated")

    async def get_user(self, user_id: str) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: str, update_data: UserUpdate) -> UserResponse:
        """Update user profile. Verifies current password when changing password."""
        if update_data.password:
            if not update_data.current_password:
                raise WrongCurrentPassword()

            user_in_db = await self.repo.get_by_id(user_id)
            if not user_in_db:
                raise UserNotFound()

            if not verify_password(update_data.current_password, user_in_db.password_hash):
                raise WrongCurrentPassword()

            from app.core.security import hash_password
            update_data = update_data.model_copy(
                update={"password_hash": hash_password(update_data.password)}
            )

        user = await self.repo.update(user_id, update_data)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: str) -> None:
        deleted = await self.repo.delete(user_id)
        if not deleted:
            raise UserNotFound()


# --- Dependency injection ---

def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db.users)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserService:
    return UserService(repo, db)