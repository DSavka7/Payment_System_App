from fastapi import APIRouter, Depends, status
from typing import List

from app.services.account_service import AccountService, get_account_service
from app.models.account_models import AccountCreate, AccountResponse, AccountUpdate


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountCreate,
    service: AccountService = Depends(get_account_service)
):
    return await service.create_account(account)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    service: AccountService = Depends(get_account_service)
):
    return await service.get_account(account_id)


@router.get("/user/{user_id}", response_model=List[AccountResponse])
async def get_user_accounts(
    user_id: str,
    service: AccountService = Depends(get_account_service)
):
    return await service.get_user_accounts(user_id)


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    update_data: AccountUpdate,
    service: AccountService = Depends(get_account_service)
):
    return await service.update_account(account_id, update_data)