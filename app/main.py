
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.database import lifespan

from app.routers.user_router import router as user_router
from app.routers.account_router import router as account_router
from app.routers.transaction_router import router as transaction_router
from app.routers.request_router import router as request_router

# Логування ініціалізується до створення app
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    lifespan=lifespan,
    title=settings.app_title,
    version=settings.app_version,
    description="""
## Payment System API

REST API банківської системи, аналог Монобанку.

### Ролі
- **USER** — реєстрація, керування своїми рахунками, перекази, запити до адміна
- **ADMIN** — управління користувачами, рахунками, розгляд запитів

### Логіка блокування рахунку
1. Користувач блокує свій рахунок: `PATCH /accounts/{id}/block`
2. Розблокувати самостійно **неможливо**
3. Потрібно подати запит: `POST /requests/` з типом `UNBLOCK`
4. Адмін схвалює: `PATCH /requests/{id}/status`
5. Рахунок автоматично розблоковується
    """,
)


# ─── Глобальна обробка помилок ────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Перехоплює будь-який необроблений виняток.
    Кінцевий користувач не бачить stack trace.
    """
    logger.error(
        "Необроблений виняток: %s %s → %s: %s",
        request.method, request.url.path, type(exc).__name__, exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка сервера. Спробуйте пізніше."},
    )


# ─── Роутери ──────────────────────────────────────────────────────────────────

app.include_router(user_router)
app.include_router(account_router)
app.include_router(transaction_router)
app.include_router(request_router)


@app.get("/", tags=["health"])
async def root():
    """Health-check ендпоінт."""
    return {
        "status": "running",
        "app": settings.app_title,
        "version": settings.app_version,
    }