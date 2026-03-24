from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.services.user_service import UserService, get_user_service
from app.models.user_models import UserCreate, UserResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(user)


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service)
):
    # form_data.username = email, form_data.password = пароль
    return await service.authenticate(form_data.username, form_data.password)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service)
):
    return await service.get_user(user_id)