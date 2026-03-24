from fastapi import HTTPException, status
from typing import Optional


class UserAlreadyExists(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує"
        )


class UserNotFound(HTTPException):
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or "Користувача не знайдено"
        )


class AccountNotFound(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рахунок не знайдено"
        )


class TransactionNotFound(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакцію не знайдено"
        )


class RequestNotFound(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запит не знайдено"
        )


class InvalidCredentials(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірні дані для входу",
            headers={"WWW-Authenticate": "Bearer"}
        )


class InsufficientFunds(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостатньо коштів на рахунку"
        )