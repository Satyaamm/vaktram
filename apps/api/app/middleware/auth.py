"""JWT verification middleware."""

from __future__ import annotations

import logging

import jwt
from fastapi import HTTPException, Request, status

from app.utils.security import decode_token

logger = logging.getLogger(__name__)


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

    try:
        payload = decode_token(token)
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

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    return payload
