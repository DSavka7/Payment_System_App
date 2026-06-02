from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_user_id
from app.models.user_models import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register new user")
async def create_user(user: UserCreate, service: UserService = Depends(get_user_service)) -> UserResponse:
    return await service.create_user(user)


@router.post("/login", summary="Login and get JWT tokens")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), service: UserService = Depends(get_user_service)):
    return await service.authenticate(form_data.username, form_data.password)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Logout")
async def logout(payload: dict, service: UserService = Depends(get_user_service)):
    rt = payload.get("refresh_token", "")
    if rt:
        await service.logout(rt)


@router.post("/refresh", summary="Refresh access token")
async def refresh_token(payload: dict, service: UserService = Depends(get_user_service)):
    rt = payload.get("refresh_token", "")
    return await service.refresh(rt)


# Static GET routes must come before /{user_id}
@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_me(user_id: str = Depends(get_current_user_id), service: UserService = Depends(get_user_service)) -> UserResponse:
    return await service.get_user(user_id)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
async def get_user(user_id: str, service: UserService = Depends(get_user_service)) -> UserResponse:
    return await service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user profile")
async def update_user(user_id: str, update_data: UserUpdate, service: UserService = Depends(get_user_service)) -> UserResponse:
    return await service.update_user(user_id, update_data)