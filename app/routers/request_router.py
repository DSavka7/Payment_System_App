from fastapi import APIRouter, Depends, status
from typing import List

from app.services.request_service import RequestService, get_request_service
from app.models.request_models import RequestCreate, RequestResponse, RequestUpdate


router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("/", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    request: RequestCreate,
    service: RequestService = Depends(get_request_service)
):
    return await service.create_request(request)


@router.get("/{request_id}", response_model=RequestResponse)
async def get_request(
    request_id: str,
    service: RequestService = Depends(get_request_service)
):
    return await service.get_request(request_id)


@router.get("/user/{user_id}", response_model=List[RequestResponse])
async def get_user_requests(
    user_id: str,
    service: RequestService = Depends(get_request_service)
):
    return await service.get_user_requests(user_id)


@router.patch("/{request_id}/status", response_model=RequestResponse)
async def update_request_status(
    request_id: str,
    update: RequestUpdate,
    service: RequestService = Depends(get_request_service)
):
    return await service.update_request_status(request_id, update)