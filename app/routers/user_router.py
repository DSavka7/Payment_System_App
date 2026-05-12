"""
Роутер для управління користувачами.
"""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_user_payload, get_current_user_id
from app.models.user_models import UserCreate, UserResponse, UserUpdate, BlockedUserInfo
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
    return await service.create_user(user)


@router.post(
    "/login",
    summary="Вхід у систему (отримання JWT-токена)",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
):
    return await service.authenticate(form_data.username, form_data.password)


@router.post(
    "/refresh",
    summary="Оновлення access token",
)
async def refresh_token(
    body: dict,
    service: UserService = Depends(get_user_service),
):
    return await service.refresh(body.get("refresh_token", ""))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Вихід із системи",
)
async def logout(
    body: dict,
    service: UserService = Depends(get_user_service),
):
    await service.logout(body.get("refresh_token", ""))


@router.get(
    "/me",
    summary="Профіль поточного користувача",
    description=(
        "Повертає профіль поточного авторизованого користувача.\n\n"
        "Якщо акаунт заблоковано — повертає HTTP 403 з полями `block_reason` та `message`."
    ),
    responses={
        200: {"description": "Профіль користувача"},
        403: {"description": "Акаунт заблоковано"},
    },
)
async def get_me(
    payload: dict = Depends(get_current_user_payload),
    service: UserService = Depends(get_user_service),
):
    """
    Повертає профіль користувача.
    Якщо заблоковано — повертає 403 з причиною блокування,
    щоб фронтенд міг показати сторінку блокування.
    """
    return await service.get_me(payload.get("sub"))


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Отримання даних користувача за ID",
)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
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
    return await service.update_user(user_id, update_data)