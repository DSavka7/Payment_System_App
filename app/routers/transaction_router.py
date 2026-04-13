
from fastapi import APIRouter, Depends, status, Query

from app.core.dependencies import get_current_user_id
from app.models.transaction_models import (
    TransactionCreate,
    TransactionResponse,
    PaginatedTransactions,
)
from app.services.transaction_service import TransactionService, get_transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити транзакцію / Create transaction",
)
async def create_transaction(
    transaction: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
    _: str = Depends(get_current_user_id),
) -> TransactionResponse:
    return await service.create_transaction(transaction)


@router.get(
    "/account/{account_id}",
    response_model=PaginatedTransactions,
    summary="Транзакції рахунку / Account transactions",
)
async def get_account_transactions(
    account_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: TransactionService = Depends(get_transaction_service),
    _: str = Depends(get_current_user_id),
) -> PaginatedTransactions:
    return await service.get_account_transactions(account_id, limit, offset)


@router.get(
    "/{tx_id}",
    response_model=TransactionResponse,
    summary="Отримати транзакцію / Get transaction",
)
async def get_transaction(
    tx_id: str,
    service: TransactionService = Depends(get_transaction_service),
    _: str = Depends(get_current_user_id),
) -> TransactionResponse:
    return await service.get_transaction(tx_id)