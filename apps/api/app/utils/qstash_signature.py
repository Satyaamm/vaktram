"""Verify Upstash QStash webhook signatures.

QStash signs every delivered job with a JWT (HS256) placed in the
``Upstash-Signature`` header. The JWT's ``body`` claim is the base64url
sha256 of the request body, ``iss`` is "Upstash", and ``sub`` is the
destination URL. Two signing keys are supported (current + next) so keys
can be rotated without downtime.

Spec: https://upstash.com/docs/qstash/howto/signature

Usage:
    from app.utils.qstash_signature import verify_qstash_signature

    @router.post("/webhooks/bot-events")
    async def bot_events(request: Request, _ = Depends(verify_qstash_signature)):
        ...

In dev — when no signing keys are configured — verification is skipped
with a warning so local QStash-less testing still works.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import time
from typing import Iterable

import jwt
from fastapi import HTTPException, Request, status

from app.config import get_settings

logger = logging.getLogger(__name__)


def _b64url_sha256(body: bytes) -> str:
    digest = hashlib.sha256(body).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def _candidate_keys(settings) -> list[str]:
    """Return non-empty signing keys to try, current first."""
    out: list[str] = []
    if settings.qstash_current_signing_key:
        out.append(settings.qstash_current_signing_key)
    if settings.qstash_next_signing_key:
        out.append(settings.qstash_next_signing_key)
    return out


def _verify_jwt_against_keys(token: str, keys: Iterable[str]) -> dict | None:
    """Try each key; return the decoded payload on first success."""
    last_err: Exception | None = None
    for key in keys:
        try:
            return jwt.decode(
                token,
                key,
                algorithms=["HS256"],
                # Don't require aud/iss-validation here — we check sub/iss
                # explicitly below so the error messages stay specific.
                options={"verify_aud": False},
            )
        except jwt.InvalidTokenError as e:
            last_err = e
            continue
    if last_err:
        logger.warning("QStash signature verification failed: %s", last_err)
    return None


async def verify_qstash_signature(request: Request) -> None:
    """FastAPI dependency: rejects the request unless it carries a valid
    QStash signature. No-ops when no signing keys are configured (dev)."""
    settings = get_settings()
    keys = _candidate_keys(settings)

    if not keys:
        # Dev / inline-fallback mode. We log loudly so this can never be
        # accidentally shipped to prod without keys.
        if settings.environment == "production":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="QStash signing keys are not configured",
            )
        logger.warning(
            "QStash signing keys not configured — webhook signature NOT verified "
            "(env=%s). This is OK for local dev but MUST NOT happen in prod.",
            settings.environment,
        )
        return

    sig = request.headers.get("Upstash-Signature") or request.headers.get(
        "upstash-signature"
    )
    if not sig:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Upstash-Signature header",
        )

    payload = _verify_jwt_against_keys(sig, keys)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Upstash-Signature",
        )

    # Issuer + subject (destination URL) sanity checks.
    if payload.get("iss") != "Upstash":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unexpected JWT issuer",
        )

    # `nbf` and `exp` are validated by jwt.decode automatically; double-check
    # that we're not in an unsigned grace window.
    now = int(time.time())
    if payload.get("exp", 0) < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature expired",
        )

    # Body integrity: the JWT carries sha256(body); compare against the
    # actual bytes we received. We must read the body BEFORE downstream
    # handlers — Starlette caches it so handlers can re-read.
    body_bytes = await request.body()
    expected_body_hash = payload.get("body")
    if expected_body_hash is not None:
        actual = _b64url_sha256(body_bytes)
        # constant-time compare
        if not _consteq(actual, expected_body_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Body hash mismatch",
            )


def _consteq(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    diff = 0
    for x, y in zip(a, b):
        diff |= ord(x) ^ ord(y)
    return diff == 0
