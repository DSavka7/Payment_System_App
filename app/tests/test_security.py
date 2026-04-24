"""
Юніт-тести для модуля безпеки (хешування, JWT).
"""
import pytest
from unittest.mock import patch
from datetime import timedelta

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


class TestPasswordHashing:
    def test_hash_is_not_plain(self):
        hashed = hash_password("MySecret@1")
        assert hashed != "MySecret@1"

    def test_verify_correct_password(self):
        hashed = hash_password("MySecret@1")
        assert verify_password("MySecret@1", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("MySecret@1")
        assert verify_password("WrongPass", hashed) is False

    def test_different_hashes_for_same_password(self):
        # bcrypt генерує різну сіль кожного разу
        h1 = hash_password("MySecret@1")
        h2 = hash_password("MySecret@1")
        assert h1 != h2


class TestJWT:
    def test_create_and_decode_token(self):
        data = {"sub": "user123", "role": "USER"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "USER"

    def test_expired_token_returns_none(self):
        data = {"sub": "user123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        result = decode_access_token(token)
        assert result is None

    def test_invalid_token_returns_none(self):
        result = decode_access_token("completely.invalid.token")
        assert result is None

    def test_token_contains_exp(self):
        token = create_access_token({"sub": "abc"})
        decoded = decode_access_token(token)
        assert "exp" in decoded