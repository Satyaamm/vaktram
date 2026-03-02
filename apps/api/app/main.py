"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.middleware.cors import add_cors_middleware
from app.utils.database import dispose_engine

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("Starting Vaktram API (%s)", settings.environment)
    yield
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

# ── Middleware ──────────────────────────────────────────────────────────
add_cors_middleware(app)

# Rate limiting (only when Redis is configured)
if settings.upstash_redis_url and settings.upstash_redis_token:
    from app.middleware.rate_limit import RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware)

# ── Routers ────────────────────────────────────────────────────────────
from app.routers import (
    health,
    internal,
    meetings,
    transcripts,
    summaries,
    search,
    bot,
    ai_config,
    analytics,
    teams,
    calendar,
    webhooks,
    ws,
)

API_PREFIX = "/api/v1"

app.include_router(health.router)  # /health at root level
app.include_router(meetings.router, prefix=API_PREFIX)
app.include_router(transcripts.router, prefix=API_PREFIX)
app.include_router(summaries.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(bot.router, prefix=API_PREFIX)
app.include_router(ai_config.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(teams.router, prefix=API_PREFIX)
app.include_router(calendar.router, prefix=API_PREFIX)
app.include_router(webhooks.router, prefix=API_PREFIX)
app.include_router(internal.router)  # No auth -- internal Docker network only
app.include_router(ws.router)  # WebSocket -- no API prefix
