
import pymongo
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class Database:

    client: AsyncIOMotorClient
    db: AsyncIOMotorDatabase

    def __init__(self) -> None:
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        self.db = self.client[settings.mongodb_db_name]

    # ── Колекції ──────────────────────────────────────────────────────────────

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
        return self.db.refresh_tokens

    # ── Індекси ───────────────────────────────────────────────────────────────

    async def create_indexes(self) -> None:
        logger.info("Перевірка/створення індексів MongoDB...")

        try:

            old_index_names = ["unique_user_card", "user_id_1_card_number_1"]
            for idx_name in old_index_names:
                try:
                    await self.accounts.drop_index(idx_name)
                    logger.info(f"Старий індекс '{idx_name}' успішно видалено")
                except Exception:
                    pass


            await self.accounts.create_index(
                [("user_id", pymongo.ASCENDING), ("card_number_full", pymongo.ASCENDING)],
                unique=True,
                name="unique_user_card_full",
                background=True
            )

            # Базовые индексы
            await self.users.create_index("email", unique=True, name="unique_email")

            simple_indexes = [
                ("users", "role", "idx_user_role"),
                ("users", "status", "idx_user_status"),
                ("accounts", "user_id", "idx_account_user"),
                ("accounts", "status", "idx_account_status"),
                ("transactions", "created_at", "idx_tx_date"),
                ("transactions", "from_account_id", "idx_tx_from"),
                ("transactions", "to_account_id", "idx_tx_to"),
                ("requests", "created_at", "idx_req_date"),
            ]

            for col_name, key, name in simple_indexes:
                col = getattr(self, col_name)
                try:
                    await col.create_index(key, name=name, background=True)
                except Exception as exc:
                    if "already exists" not in str(exc).lower():
                        logger.warning("Помилка індексу %s: %s", name, exc)


            try:
                await self.requests.create_index(
                    [("user_id", pymongo.ASCENDING), ("status", pymongo.ASCENDING)],
                    name="idx_req_user_status",
                    background=True
                )
            except Exception:
                pass

            logger.info("Індекси успішно перевірені / створені")

        except Exception as exc:
            logger.error("Критична помилка при створенні індексів: %s", exc)
            raise

    async def close(self) -> None:
        if self.client:
            self.client.close()
            logger.info("Підключення до MongoDB закрито")


# ── Глобальний singleton ───────────────────────────────────────────────────────
db = Database()


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    try:
        await db.client.admin.command("ping")
        logger.info("Успішно підключено до MongoDB (%s)", settings.mongodb_db_name)
        await db.create_indexes()
    except Exception as exc:
        logger.critical("Не вдалося підключитися до MongoDB: %s", exc)
        raise

    yield

    # Shutdown
    await db.close()


# ── Dependency Injection ───────────────────────────────────────────────────────

async def get_db() -> AsyncIOMotorDatabase:
    return db.db