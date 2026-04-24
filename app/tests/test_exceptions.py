"""
Юніт-тести для ієрархії винятків застосунку.
"""
import pytest
from fastapi import status

from app.core.exceptions import (
    BaseAppException,
    UserAlreadyExists,
    UserNotFound,
    UserInactive,
    AccountNotFound,
    AccountBlocked,
    InsufficientFunds,
    TransactionNotFound,
    RequestNotFound,
    InvalidCredentials,
    Forbidden,
    InvalidObjectId,
)


class TestExceptionHierarchy:
    def test_user_already_exists_is_base(self):
        exc = UserAlreadyExists()
        assert isinstance(exc, BaseAppException)
        assert exc.status_code == status.HTTP_409_CONFLICT

    def test_user_not_found_default_detail(self):
        exc = UserNotFound()
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "не знайдено" in exc.detail

    def test_user_not_found_custom_detail(self):
        exc = UserNotFound(detail="Нестандартне повідомлення")
        assert exc.detail == "Нестандартне повідомлення"

    def test_account_not_found(self):
        exc = AccountNotFound()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_account_blocked(self):
        exc = AccountBlocked()
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_insufficient_funds(self):
        exc = InsufficientFunds()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_credentials_has_www_authenticate(self):
        exc = InvalidCredentials()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.headers is not None
        assert "WWW-Authenticate" in exc.headers

    def test_forbidden_default(self):
        exc = Forbidden()
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert "заборонено" in exc.detail

    def test_forbidden_custom(self):
        exc = Forbidden("Тільки адміністратор")
        assert exc.detail == "Тільки адміністратор"

    def test_invalid_object_id(self):
        exc = InvalidObjectId("user_id")
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert "user_id" in exc.detail

    def test_transaction_not_found(self):
        exc = TransactionNotFound()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_request_not_found(self):
        exc = RequestNotFound()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_user_inactive(self):
        exc = UserInactive()
        assert exc.status_code == status.HTTP_403_FORBIDDEN