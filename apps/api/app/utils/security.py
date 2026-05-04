"""Password hashing and JWT token utilities."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from app.config import get_settings

settings = get_settings()

# JWT_SECRET MUST be set explicitly in the environment. We never fall back to
# the Fernet encryption key — separating signing and encryption material is a
# basic hygiene rule (rotation, blast radius, algorithm-confusion defenses).
# config._validate_jwt_secret enforces this at startup; the assert below is a
# defense-in-depth tripwire if config validation is ever weakened.
assert settings.jwt_secret, (
    "JWT_SECRET is empty at import time — config validation should have rejected this"
)
JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 1
BCRYPT_ROUNDS = 12

# A pre-computed bcrypt hash of a long random password we never use. When a
# login lookup misses, we still call bcrypt against this so timing reveals
# nothing about whether the email exists. Computed once at import.
_DUMMY_PASSWORD_HASH: str = bcrypt.hashpw(
    secrets.token_urlsafe(32).encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def dummy_verify(password: str) -> bool:
    """Run bcrypt against a constant dummy hash so a missing-user path takes
    the same wall-clock time as a real password check. Always returns False."""
    bcrypt.checkpw(password.encode(), _DUMMY_PASSWORD_HASH.encode())
    return False


def create_access_token(user_id: uuid.UUID, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str]:
    """Returns (token, jti). The jti is what we track for rotation/revocation."""
    now = datetime.now(timezone.utc)
    jti = secrets.token_urlsafe(16)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": jti,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), jti


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Pins HS256 explicitly so an attacker cannot
    submit a token with `alg: none` or RS256 to bypass HMAC verification."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
