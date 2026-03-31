from fastapi import HTTPException, status
from typing import Optional


class UserAlreadyExists(HTTPException):
    """Спроба зареєструвати email, що вже існує в системі."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує"
        )


class UserNotFound(HTTPException):
    """Користувача з вказаним ідентифікатором не знайдено."""
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or "Користувача не знайдено"
        )


class AccountNotFound(HTTPException):
    """Рахунок з вказаним ідентифікатором не знайдено."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рахунок не знайдено"
        )


class AccountBlocked(HTTPException):
    """Операція заборонена — рахунок заблоковано."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Рахунок заблоковано. Зверніться до служби підтримки"
        )


class TransactionNotFound(HTTPException):
    """Транзакцію з вказаним ідентифікатором не знайдено."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакцію не знайдено"
        )


class RequestNotFound(HTTPException):
    """Запит з вказаним ідентифікатором не знайдено."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запит не знайдено"
        )


class InvalidCredentials(HTTPException):
    """Невірний email або пароль при автентифікації."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірні дані для входу",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InsufficientFunds(HTTPException):
    """На рахунку недостатньо коштів для виконання операції."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостатньо коштів на рахунку"
        )


class InsufficientPermissions(HTTPException):
    """Користувач не має прав для виконання даної операції."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав для виконання операції"
        )


class UserBlocked(HTTPException):
    """Обліковий запис користувача заблоковано адміністратором."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Обліковий запис заблоковано. Зверніться до служби підтримки"
        )


class InvalidAccountOwnership(HTTPException):
    """Користувач намагається отримати доступ до чужого рахунку."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ до цього рахунку заборонено"
        )


class TransferToSameAccount(HTTPException):
    """Спроба переказу на той самий рахунок."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неможливо здійснити переказ на той самий рахунок"
        )


class CurrencyMismatch(HTTPException):
    """Валюти рахунків не збігаються при переказі."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Валюти рахунків відправника та отримувача не збігаються"
        )


class DuplicateRequest(HTTPException):
    """Активний запит для цього рахунку вже існує."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Активний запит для цього рахунку вже існує"
        )


class AccountAlreadyBlocked(HTTPException):
    """Спроба заблокувати вже заблокований рахунок."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Рахунок вже заблоковано"
        )


class AccountAlreadyActive(HTTPException):
    """Спроба розблокувати вже активний рахунок."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Рахунок вже активний"
        )


class UnblockRequiresRequest(HTTPException):
    """Розблокування можливе лише через запит до адміністратора."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Для розблокування рахунку необхідно подати запит до адміністратора"
        )