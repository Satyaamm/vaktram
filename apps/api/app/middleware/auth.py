"""Supabase JWT verification middleware."""

from __future__ import annotations

import jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


def decode_supabase_jwt(token: str) -> dict:
    """Decode and verify a Supabase-issued JWT.

    Returns the decoded payload or raises HTTPException on failure.
    """
    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured",
        )
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )


async def get_current_user_from_token(request: Request) -> dict:
    """Extract and verify the JWT from the Authorization header.

    Returns the decoded JWT payload (contains ``sub``, ``email``, etc.).
    """
    auth: str | None = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = auth.split(" ", 1)[1]
    return decode_supabase_jwt(token)
