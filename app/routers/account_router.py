from typing import List

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_active_user, get_current_user_payload
from app.models.account_models import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    TransferRequest,
)
from app.models.transaction_models import TransactionResponse
from app.services.account_service import AccountService, get_account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new account",
)
async def create_account(
    account: AccountCreate,
    _: str = Depends(get_active_user),
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    return await service.create_account(account)


@router.post(
    "/transfer",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Transfer funds between accounts",
)
async def transfer(
    request: TransferRequest,
    payload: dict = Depends(get_current_user_payload),
    service: AccountService = Depends(get_account_service),
) -> TransactionResponse:
    user_id = payload.get("sub")
    return await service.transfer(request, user_id)


@router.get(
    "/user/{user_id}",
    response_model=List[AccountResponse],
    summary="Get all accounts for a user",
)
async def get_user_accounts(
    user_id: str,
    _: str = Depends(get_active_user),
    service: AccountService = Depends(get_account_service),
) -> List[AccountResponse]:
    return await service.get_user_accounts(user_id)


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Get account by ID",
)
async def get_account(
    account_id: str,
    _: str = Depends(get_active_user),
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    return await service.get_account(account_id)


@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Update account status or balance",
)
async def update_account(
    account_id: str,
    update_data: AccountUpdate,
    _: str = Depends(get_active_user),
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    return await service.update_account(account_id, update_data)