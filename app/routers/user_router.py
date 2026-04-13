
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_user_id, require_admin
from app.services.user_service import UserService, get_user_service
from app.models.user_models import (
    UserCreate,
    UserResponse,
    UserUpdate,
    TokenResponse,
    RefreshRequest,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Реєстрація нового користувача / Register new user",
)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Реєструє нового користувача у системі."""
    return await service.create_user(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вхід у систему / Login",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
) -> TokenResponse:
    return await service.authenticate(form_data.username, form_data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Оновлення access token / Refresh access token",
)
async def refresh_token(
    request: RefreshRequest,
    service: UserService = Depends(get_user_service),
) -> TokenResponse:
    """Видає новий access token за валідним refresh token."""
    return await service.refresh_access_token(request)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Вихід із системи / Logout",
)
async def logout(
    request: RefreshRequest,
    service: UserService = Depends(get_user_service),
) -> None:
    """Відкликає refresh token (завершує сесію)."""
    await service.logout(request.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Мій профіль / My profile",
)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Повертає профіль поточного авторизованого користувача."""
    return await service.get_user(user_id)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Отримати користувача за ID / Get user by ID",
)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    _: dict = Depends(require_admin),
) -> UserResponse:
    """Повертає дані користувача за ID (тільки для адміністраторів)."""
    return await service.get_user(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Оновити користувача / Update user",
)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    service: UserService = Depends(get_user_service),
    _: dict = Depends(require_admin),
) -> UserResponse:
    """Оновлює дані користувача (тільки для адміністраторів)."""
    return await service.update_user(user_id, update_data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити користувача / Delete user",
)
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    _: dict = Depends(require_admin),
) -> None:
    """Видаляє користувача (тільки для адміністраторів)."""
    await service.delete_user(user_id)