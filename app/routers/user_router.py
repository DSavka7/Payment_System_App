
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_user_id
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
    """Автентифікує користувача та повертає JWT-токен доступу."""
    return await service.authenticate(form_data.username, form_data.password)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Отримання даних поточного користувача",
)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Повертає дані авторизованого користувача з JWT-токена."""
    return await service.get_user(user_id)


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