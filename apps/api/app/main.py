"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.config import get_settings
from app.middleware.cors import add_cors_middleware
from app.middleware.request_context import RequestContextMiddleware
from app.utils.database import dispose_engine
from app.utils.observability import init_observability

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    from app.services.encryption_service import EncryptionService
    from app.services.meeting_scheduler import start_scheduler, stop_scheduler

    logger.info("Starting Vaktram API (%s)", settings.environment)

    # Validate ENCRYPTION_KEY immediately — Fernet raises if the key is
    # missing or malformed. Without this guard the failure surfaces only
    # when the first user-AI-config is decrypted, which may not happen
    # until hours after deploy.
    try:
        EncryptionService()
    except Exception as exc:
        logger.critical("ENCRYPTION_KEY is invalid: %s", exc)
        raise

    # Start APScheduler
    await start_scheduler()

    yield

    # Stop APScheduler
    await stop_scheduler()

    logger.info("Shutting down Vaktram API")
    await dispose_engine()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# ── Observability (logging, Sentry, OTel) ────────────────────────────
init_observability(app)

# ── Middleware ──────────────────────────────────────────────────────────
add_cors_middleware(app)
app.add_middleware(RequestContextMiddleware)

# Rate limiting (only when Redis is configured)
if settings.upstash_redis_url and settings.upstash_redis_token:
    from app.middleware.rate_limit import RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware)

# ── Routers ────────────────────────────────────────────────────────────
from app.routers import (
    auth,
    health,
    internal,
    meetings,
    transcripts,
    summaries,
    search,
    bot,
    ai_config,
    analytics,
    notifications,
    teams,
    calendar,
    webhooks,
    ws,
    billing,
    sso,
    scim,
    compliance,
    ask,
    topics,
    channels,
    soundbites,
    integrations,
    webhooks_outbound,
)

API_PREFIX = "/api/v1"

app.include_router(health.router)  # /health at root level
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(meetings.router, prefix=API_PREFIX)
app.include_router(transcripts.router, prefix=API_PREFIX)
app.include_router(summaries.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(bot.router, prefix=API_PREFIX)
app.include_router(ai_config.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(teams.router, prefix=API_PREFIX)
app.include_router(calendar.router, prefix=API_PREFIX)
app.include_router(webhooks.router, prefix=API_PREFIX)
app.include_router(billing.router, prefix=API_PREFIX)
app.include_router(sso.router, prefix=API_PREFIX)
app.include_router(scim.router, prefix=API_PREFIX)
app.include_router(compliance.router, prefix=API_PREFIX)
app.include_router(ask.router, prefix=API_PREFIX)
app.include_router(topics.router, prefix=API_PREFIX)
app.include_router(channels.router, prefix=API_PREFIX)
app.include_router(soundbites.router, prefix=API_PREFIX)
app.include_router(integrations.router, prefix=API_PREFIX)
app.include_router(webhooks_outbound.router, prefix=API_PREFIX)
app.include_router(internal.router)  # No auth -- internal Docker network only
app.include_router(ws.router)  # WebSocket -- no API prefix


# ── Custom OpenAPI schema with OAuth2 password flow for Swagger UI ────
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/auth/token",
                    "scopes": {},
                }
            },
        }
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi  # type: ignore[assignment]
