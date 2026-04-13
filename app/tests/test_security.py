
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id_from_token,
)
from app.core.exceptions import TokenExpired, InvalidToken


class TestPasswordHashing:
    """Тести хешування паролів."""

    def test_hash_password_returns_string(self):
        hashed = hash_password("mypassword123")
        assert isinstance(hashed, str)

    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"

    def test_verify_correct_password(self):
        hashed = hash_password("securepass")
        assert verify_password("securepass", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("securepass")
        assert verify_password("wrongpass", hashed) is False

    def test_same_password_different_hashes(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


class TestJWT:
    """Тести JWT access та refresh токенів."""

    def test_create_and_decode_access_token(self):
        payload = {"sub": "user123", "role": "USER"}
        token = create_access_token(payload)
        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "USER"

    def test_create_and_decode_refresh_token(self):
        payload = {"sub": "user456", "role": "ADMIN"}
        token = create_refresh_token(payload)
        decoded = decode_token(token)
        assert decoded["sub"] == "user456"
        assert decoded["type"] == "refresh"

    def test_access_token_has_no_refresh_type(self):
        token = create_access_token({"sub": "u1"})
        decoded = decode_token(token)
        assert decoded.get("type") != "refresh"

    def test_invalid_token_raises(self):
        with pytest.raises(InvalidToken):
            decode_token("this.is.not.valid")

    def test_get_user_id_from_token(self):
        token = create_access_token({"sub": "abc123", "role": "USER"})
        user_id = get_user_id_from_token(token)
        assert user_id == "abc123"

    def test_get_user_id_missing_sub_raises(self):
        token = create_access_token({"role": "USER"})
        with pytest.raises(InvalidToken):
            get_user_id_from_token(token)