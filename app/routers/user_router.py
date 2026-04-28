"""
Роутер для управління користувачами.
Обробляє HTTP-запити реєстрації, входу та отримання профілю.
"""
from typing import List

from fastapi import APIRouter, Depends, Query, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_user_id, require_admin
from app.models.user_models import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Реєстрація нового користувача",
)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Реєструє нового користувача в системі."""
    return await service.create_user(user)


@router.post(
    "/login",
    summary="Вхід у систему (отримання JWT-токена)",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
):
    """Автентифікує користувача та повертає JWT access + refresh токени."""
    return await service.authenticate(form_data.username, form_data.password)


@router.post(
    "/refresh",
    summary="Оновлення access токена за допомогою refresh токена",
)
async def refresh_token(
    payload: dict,
    service: UserService = Depends(get_user_service),
):
    """Видає новий access токен за дійсним refresh токеном (PB-03)."""
    return await service.refresh_access_token(payload.get("refresh_token", ""))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Вихід із системи (інвалідація refresh токена)",
)
async def logout(
    payload: dict,
    service: UserService = Depends(get_user_service),
):
    """Інвалідує refresh токен поточного сеансу."""
    await service.logout(payload.get("refresh_token", ""))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Отримання профілю поточного користувача (PB-11)",
)
async def get_me(
    current_user_id: str = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Повертає дані авторизованого користувача."""
    return await service.get_user(current_user_id)


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="[ADMIN] Список усіх користувачів з пагінацією",
)
async def get_all_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _admin: dict = Depends(require_admin),
    service: UserService = Depends(get_user_service),
) -> List[UserResponse]:
    """Повертає список усіх користувачів (тільки для адміністратора)."""
    return await service.get_all_users(limit=limit, offset=offset)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Отримання даних користувача за ID",
)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Повертає дані користувача за його ідентифікатором."""
    return await service.get_user(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Оновлення профілю користувача",
)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Оновлює дані профілю користувача (телефон, ім'я, статус)."""
    return await service.update_user(user_id, update_data)
