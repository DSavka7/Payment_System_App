
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.core.logging_config import setup_logging
from app.db.database import lifespan
from app.routers.account_router import router as account_router
from app.routers.request_router import router as request_router
from app.routers.transaction_router import router as transaction_router
from app.routers.user_router import router as user_router

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    lifespan=lifespan,
    title="Payment System API",
    description="Банківська система / Banking system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("AppException [%s] %s %s → %s",
                   exc.status_code, request.method, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Помилка валідації / Validation error", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутрішня помилка сервера / Internal server error"},
    )


app.include_router(user_router)
app.include_router(account_router)
app.include_router(transaction_router)
app.include_router(request_router)


@app.get("/", tags=["health"])
async def root() -> dict:
    return {"status": "ok", "message": "Payment System API is running", "docs": "/docs"}