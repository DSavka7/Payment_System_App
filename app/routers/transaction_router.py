from typing import List

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_active_user
from app.models.transaction_models import TransactionCreate, TransactionResponse
from app.services.transaction_service import TransactionService, get_transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, summary="Create transaction")
async def create_transaction(
    transaction: TransactionCreate,
    _: str = Depends(get_active_user),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    return await service.create_transaction(transaction)


@router.get("/account/{account_id}", summary="Get account transactions with pagination")
async def get_account_transactions(
    account_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: str = Depends(get_active_user),
    service: TransactionService = Depends(get_transaction_service),
):
    return await service.get_account_transactions(account_id, limit=limit, offset=offset)


@router.get("/{tx_id}", response_model=TransactionResponse, summary="Get transaction by ID")
async def get_transaction(
    tx_id: str,
    _: str = Depends(get_active_user),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    return await service.get_transaction(tx_id)