"""
Роутер для операцій з банківськими рахунками.
ВАЖЛИВО: статичні маршрути (/transfer, /user/{id}) мають бути
ПЕРЕД динамічними (/{account_id}) щоб FastAPI не плутав їх.
"""
from typing import List

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user_id, require_admin
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
    summary="Створити рахунок / Create account",
)
async def create_account(
    account: AccountCreate,
    service: AccountService = Depends(get_account_service),
    _: str = Depends(get_current_user_id),
) -> AccountResponse:
    return await service.create_account(account)


# !! /transfer МАЄ бути перед /{account_id} !!
@router.post(
    "/transfer",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Переказ між рахунками / Transfer between accounts",
)
async def transfer(
    transfer_request: TransferRequest,
    service: AccountService = Depends(get_account_service),
    _: str = Depends(get_current_user_id),
) -> TransactionResponse:
    return await service.transfer(transfer_request)


# !! /user/{user_id} МАЄ бути перед /{account_id} !!
@router.get(
    "/user/{user_id}",
    response_model=List[AccountResponse],
    summary="Рахунки користувача / User accounts",
)
async def get_user_accounts(
    user_id: str,
    service: AccountService = Depends(get_account_service),
    _: str = Depends(get_current_user_id),
) -> List[AccountResponse]:
    return await service.get_user_accounts(user_id)


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Отримати рахунок / Get account",
)
async def get_account(
    account_id: str,
    service: AccountService = Depends(get_account_service),
    _: str = Depends(get_current_user_id),
) -> AccountResponse:
    return await service.get_account(account_id)


@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Оновити рахунок / Update account",
)
async def update_account(
    account_id: str,
    update_data: AccountUpdate,
    service: AccountService = Depends(get_account_service),
    _: dict = Depends(require_admin),
) -> AccountResponse:
    return await service.update_account(account_id, update_data)


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити рахунок / Delete account",
)
async def delete_account(
    account_id: str,
    service: AccountService = Depends(get_account_service),
    _: dict = Depends(require_admin),
) -> None:
    return await service.delete_account(account_id)