import logging
from fastapi import APIRouter, Depends, status, Query
from typing import Dict

from app.services.transaction_service import TransactionService, get_transaction_service
from app.models.transaction_models import TransferCreate, TransactionResponse, PaginatedTransactions
from app.core.security import require_user, require_admin
from app.core.config import settings

router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = logging.getLogger(__name__)


# ─── USER ендпоінти ───────────────────────────────────────────────────────────

@router.post(
    "/transfer/{from_account_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Переказ коштів (USER)",
)
async def make_transfer(
    from_account_id: str,
    transfer: TransferCreate,
    payload: Dict = Depends(require_user),
    service: TransactionService = Depends(get_transaction_service),
):

    return await service.make_transfer(
        user_id=payload["sub"],
        from_account_id=from_account_id,
        transfer=transfer,
    )


@router.get(
    "/account/{account_id}",
    response_model=PaginatedTransactions,
    summary="Транзакції рахунку (USER/ADMIN)",
)
async def get_account_transactions(
    account_id: str,
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(0, ge=0),
    payload: Dict = Depends(require_user),
    service: TransactionService = Depends(get_transaction_service),
):
    return await service.get_account_transactions(
        account_id=account_id,
        user_id=payload["sub"],
        role=payload["role"],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{tx_id}",
    response_model=TransactionResponse,
    summary="Транзакція за ID (USER/ADMIN)",
)
async def get_transaction(
    tx_id: str,
    payload: Dict = Depends(require_user),
    service: TransactionService = Depends(get_transaction_service),
):
    """Повертає деталі транзакції. USER бачить лише свої."""
    return await service.get_transaction(
        tx_id=tx_id,
        user_id=payload["sub"],
        role=payload["role"],
    )


# ─── ADMIN ендпоінти ──────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=PaginatedTransactions,
    summary="[ADMIN] Всі транзакції",
)
async def get_all_transactions(
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(0, ge=0),
    payload: Dict = Depends(require_admin),
    service: TransactionService = Depends(get_transaction_service),
):
    """Пагінований список всіх транзакцій. Тільки для ADMIN."""
    return await service.get_all_transactions(limit=limit, offset=offset)