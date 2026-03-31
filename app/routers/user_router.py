import logging
from fastapi import APIRouter, Depends, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict

from app.services.user_service import UserService, get_user_service
from app.models.user_models import UserCreate, UserResponse, UserUpdate, TokenResponse, RefreshTokenRequest
from app.core.security import require_user, require_admin, get_current_user_payload
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


# ─── Публічні ендпоінти ────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Реєстрація нового користувача",
)
async def register(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """Публічна реєстрація. Роль USER призначається автоматично."""
    return await service.create_user(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вхід (отримання JWT токенів)",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
):
    """Автентифікація. Повертає access + refresh токени."""
    return await service.authenticate(form_data.username, form_data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Оновлення токенів за refresh token",
)
async def refresh_tokens(
    body: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    """Оновлює пару токенів за валідним refresh token."""
    return await service.refresh_tokens(body.refresh_token)


# ─── USER ендпоінти (власний профіль) ─────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Власний профіль",
)
async def get_me(
    payload: Dict = Depends(require_user),
    service: UserService = Depends(get_user_service),
):
    """Повертає профіль поточного авторизованого користувача."""
    return await service.get_user(payload["sub"])


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Редагування профілю",
)
async def update_me(
    update_data: UserUpdate,
    payload: Dict = Depends(require_user),
    service: UserService = Depends(get_user_service),
):
    """Редагує phone/first_name/last_name поточного користувача."""
    return await service.update_profile(payload["sub"], update_data)


# ─── ADMIN ендпоінти ──────────────────────────────────────────────────────────

@router.get(
    "/",
    summary="[ADMIN] Список всіх користувачів",
)
async def get_all_users(
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(0, ge=0),
    payload: Dict = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Пагінований список всіх користувачів. Тільки для ADMIN."""
    return await service.get_all_users(limit=limit, offset=offset)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="[ADMIN] Профіль користувача за ID",
)
async def get_user(
    user_id: str,
    payload: Dict = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Повертає профіль будь-якого користувача. Тільки для ADMIN."""
    return await service.get_user(user_id)


@router.patch(
    "/{user_id}/block",
    response_model=UserResponse,
    summary="[ADMIN] Заблокувати користувача",
)
async def block_user(
    user_id: str,
    payload: Dict = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Блокує обліковий запис користувача. Тільки для ADMIN."""
    return await service.block_user(admin_id=payload["sub"], user_id=user_id)


@router.patch(
    "/{user_id}/unblock",
    response_model=UserResponse,
    summary="[ADMIN] Розблокувати користувача",
)
async def unblock_user(
    user_id: str,
    payload: Dict = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Розблоковує обліковий запис. Тільки для ADMIN."""
    return await service.unblock_user(admin_id=payload["sub"], user_id=user_id)