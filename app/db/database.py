"""
Модуль підключення до MongoDB — оригінальна версія з додаванням
колекції refresh_tokens та правильними індексами.
"""
import pymongo
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class Database:
    """Singleton для управління підключенням до MongoDB."""

    client: AsyncIOMotorClient
    db: AsyncIOMotorDatabase

    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        self.db     = self.client[settings.mongodb_db_name]

    @property
    def users(self):
        return self.db.users

    @property
    def accounts(self):
        return self.db.accounts

    @property
    def transactions(self):
        return self.db.transactions

    @property
    def requests(self):
        return self.db.requests

    @property
    def refresh_tokens(self):
        """Колекція refresh токенів (потрібна для logout і refresh)."""
        return self.db.refresh_tokens

    async def create_indexes(self) -> None:
        """Створює або перевіряє індекси у всіх колекціях."""
        logger.info("Початок створення/перевірки індексів у MongoDB...")

        try:
            # Users
            await self.users.create_index("email", unique=True, name="unique_email")

            # Accounts
            await self.accounts.create_index(
                [("user_id", pymongo.ASCENDING), ("card_number", pymongo.ASCENDING)],
                unique=True, name="unique_user_card",
            )

            # Refresh tokens — TTL 7 днів
            await self.refresh_tokens.create_index(
                "created_at",
                expireAfterSeconds=7 * 24 * 3600,
                name="ttl_refresh_tokens",
            )
            await self.refresh_tokens.create_index(
                "token", unique=True, name="unique_refresh_token"
            )

            # Інші індекси
            indexes = [
                ("users",        "role",           "idx_user_role"),
                ("accounts",     "user_id",         "idx_account_user"),
                ("accounts",     "status",          "idx_account_status"),
                ("transactions", "created_at",      "idx_transaction_date"),
                ("transactions", "from_account_id", "idx_from_account"),
                ("transactions", "to_account_id",   "idx_to_account"),
                ("requests",     "created_at",      "idx_request_date"),
            ]

            for collection_name, key, name in indexes:
                collection = getattr(self, collection_name)
                try:
                    await collection.create_index(key, name=name, background=True)
                except Exception as exc:
                    if "already exists" in str(exc) or "IndexOptionsConflict" in str(exc):
                        logger.debug("Індекс %s вже існує — пропускаємо", name)
                    else:
                        logger.error("Помилка при створенні індексу %s: %s", name, exc)

            logger.info("Індекси успішно перевірені / створені")

        except Exception as exc:
            logger.error("Загальна помилка при створенні індексів: %s", exc)

    async def close(self) -> None:
        if self.client:
            self.client.close()
            logger.info("Підключення до MongoDB закрито")


# Singleton
db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await db.client.admin.command("ping")
        logger.info("Успішно підключено до MongoDB: %s", settings.mongodb_db_name)
        await db.create_indexes()
    except Exception as exc:
        logger.critical("Критична помилка підключення до MongoDB: %s", exc)
        raise

    yield

    await db.close()


async def get_db() -> AsyncIOMotorDatabase:
    return db.db