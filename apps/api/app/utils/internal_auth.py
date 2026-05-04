"""Authenticate calls FROM internal services (bot service, workers) INTO the API.

The shared secret is set as ``BOT_SHARED_SECRET`` in both:
  • The API's environment (read here)
  • The bot service's environment (forwarded on every request)
  • Each worker's environment (forwarded on every callback)

We deliberately reuse the bot secret as a single internal-services secret.
Cleaner than a sprawl of one-secret-per-service for a small platform; if the
threat model later warrants per-service keys, swap this for a JWT issuer.

Endpoints that call this dep refuse traffic from the public internet — only
peers that know the secret get through.
"""

from __future__ import annotations

import hmac
import logging

from fastapi import Header, HTTPException, status

from app.config import get_settings

logger = logging.getLogger(__name__)


def require_internal_auth(x_bot_auth: str = Header(default="")) -> None:
    settings = get_settings()
    secret = settings.bot_shared_secret
    if not secret:
        # In dev with no secret configured we let the request through but
        # warn loudly. Production refuses to boot without the secret (see
        # bot-service/main.py); the API also won't be able to dispatch to
        # the bot, so the symptom surfaces fast.
        if settings.environment == "production":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="BOT_SHARED_SECRET not configured",
            )
        logger.warning(
            "BOT_SHARED_SECRET unset; internal endpoint NOT authenticated "
            "(env=%s). DO NOT ship this to prod.", settings.environment,
        )
        return

    if not hmac.compare_digest(x_bot_auth or "", secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-Bot-Auth header",
        )
