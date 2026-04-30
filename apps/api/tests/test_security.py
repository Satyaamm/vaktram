"""Unit tests for password hashing and JWT helpers."""

from __future__ import annotations

import uuid

import jwt
import pytest

from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        h = hash_password("hunter2")
        assert h != "hunter2"
        assert h.startswith("$2")  # bcrypt prefix

    def test_verify_correct_password(self):
        h = hash_password("hunter2")
        assert verify_password("hunter2", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("hunter2")
        assert verify_password("wrong", h) is False

    def test_hashes_are_salted(self):
        assert hash_password("same") != hash_password("same")


class TestJWT:
    def test_access_token_roundtrip(self):
        uid = uuid.uuid4()
        token = create_access_token(uid, "u@example.com")
        decoded = decode_token(token)
        assert decoded["sub"] == str(uid)
        assert decoded["email"] == "u@example.com"
        assert decoded["type"] == "access"

    def test_refresh_token_has_correct_type(self):
        uid = uuid.uuid4()
        token = create_refresh_token(uid)
        decoded = decode_token(token)
        assert decoded["type"] == "refresh"

    def test_invalid_signature_rejected(self):
        token = create_access_token(uuid.uuid4(), "u@example.com")
        tampered = token[:-4] + "XXXX"
        with pytest.raises(jwt.InvalidTokenError):
            decode_token(tampered)
