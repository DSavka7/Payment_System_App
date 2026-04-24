"""
Точка входу FastAPI-застосунку платіжної системи.
Ініціалізує застосунок, підключає роутери та глобальні обробники помилок.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import BaseAppException
from app.core.logging_config import setup_logging
from app.db.database import lifespan
from app.routers.account_router import router as account_router
from app.routers.request_router import router as request_router
from app.routers.transaction_router import router as transaction_router
from app.routers.user_router import router as user_router

# Ініціалізація логування при старті модуля
setup_logging(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    lifespan=lifespan,
    title=settings.app_title,
    version=settings.app_version,
    description="REST API для платіжної системи з підтримкою кирилиці",
)

# ──────────────────────────────────────────────
# CORS middleware
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Роутери
# ──────────────────────────────────────────────
app.include_router(user_router)
app.include_router(account_router)
app.include_router(transaction_router)
app.include_router(request_router)


# ──────────────────────────────────────────────
# Глобальні обробники помилок
# ──────────────────────────────────────────────

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """Обробляє всі бізнес-помилки застосунку."""
    logger.warning(
        "Бізнес-помилка [%s] на %s %s: %s",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers or {},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Перехоплює всі необроблені винятки.
    Кінцевий користувач НЕ бачить stack trace.
    """
    logger.exception(
        "Необроблена помилка на %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка сервера. Зверніться до підтримки."},
    )


@app.get("/", tags=["health"])
async def root():
    """Health-check endpoint."""
    return {"status": "ok", "message": "Payment System API працює"}


@app.get("/health", tags=["health"])
async def health_check():
    """Детальна перевірка стану сервісу."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "service": settings.app_title,
    }