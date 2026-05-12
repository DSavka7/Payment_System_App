
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import BaseAppException
from app.core.logging_config import setup_logging
from app.db.database import lifespan
from app.routers.account_router import router as account_router
from app.routers.admin_router import router as admin_router
from app.routers.request_router import router as request_router
from app.routers.transaction_router import router as transaction_router
from app.routers.user_router import router as user_router

setup_logging(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    lifespan=lifespan,
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "REST API банківської платіжної системи.\n\n"
        "## Ролі\n"
        "- **USER** — звичайний користувач\n"
        "- **ADMIN** — адміністратор (доступ до `/admin/*`)\n\n"
        "## Підозрілі транзакції\n"
        "Перекази вище порогу (UAH ≥ 50 000 / USD ≥ 1 500 / EUR ≥ 1 400) "
        "отримують статус `pending_review` і потребують схвалення адміна."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(account_router)
app.include_router(transaction_router)
app.include_router(request_router)
app.include_router(admin_router)


@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """Обробляє всі бізнес-помилки застосунку."""
    logger.warning(
        "Бізнес-помилка [%s] на %s %s: %s",
        exc.status_code, request.method, request.url.path, exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers or {},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Перехоплює всі необроблені винятки — стек не показується користувачу."""
    logger.exception("Необроблена помилка на %s %s", request.method, request.url.path)
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