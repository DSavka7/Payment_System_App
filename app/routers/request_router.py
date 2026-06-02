from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import require_admin
from app.models.request_models import RequestCreate, RequestResponse, RequestUpdate
from app.services.request_service import RequestService, get_request_service

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("/", response_model=RequestResponse, status_code=status.HTTP_201_CREATED, summary="Create request")
async def create_request(request: RequestCreate, service: RequestService = Depends(get_request_service)) -> RequestResponse:
    return await service.create_request(request)


@router.get("/", response_model=List[RequestResponse], summary="[ADMIN] List all requests")
async def get_all_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _admin: dict = Depends(require_admin),
    service: RequestService = Depends(get_request_service),
) -> List[RequestResponse]:
    return await service.get_all_requests(status_filter=status_filter, limit=limit, offset=offset)


@router.get("/user/{user_id}", response_model=List[RequestResponse], summary="Get user requests")
async def get_user_requests(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: RequestService = Depends(get_request_service),
) -> List[RequestResponse]:
    return await service.get_user_requests(user_id, limit=limit, offset=offset)


@router.get("/{request_id}", response_model=RequestResponse, summary="Get request by ID")
async def get_request(request_id: str, service: RequestService = Depends(get_request_service)) -> RequestResponse:
    return await service.get_request(request_id)


@router.patch("/{request_id}/status", response_model=RequestResponse, summary="[ADMIN] Update request status")
async def update_request_status(
    request_id: str,
    update: RequestUpdate,
    _admin: dict = Depends(require_admin),
    service: RequestService = Depends(get_request_service),
) -> RequestResponse:
    return await service.update_request_status(request_id, update)