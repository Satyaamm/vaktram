"""
Bot Service - FastAPI application for managing meeting bots.
Provides endpoints to start/stop bots, check health, and manage sessions.

Auth model: every endpoint except /health requires the
`X-Bot-Auth` header to match `BOT_SHARED_SECRET`. The Vaktram API knows
the same secret and includes it on every dispatch. Without this gate the
service is fully exposed to the internet (port 8001 on the VPS) and any
attacker can spawn bots into arbitrary meetings or stop existing ones.
"""

import hmac
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field

from bot.orchestrator import BotOrchestrator, detect_platform

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://api:8000")
BOT_SHARED_SECRET = os.getenv("BOT_SHARED_SECRET", "").strip()
if not BOT_SHARED_SECRET:
    # Refuse to boot without a secret — the bot service is exposed publicly
    # on the VPS, so a missing secret means anyone can drive recordings.
    raise RuntimeError(
        "BOT_SHARED_SECRET must be set. Generate with: "
        "python -c 'import secrets; print(secrets.token_urlsafe(32))' "
        "and set the same value on this host AND in the API's env."
    )

orchestrator = BotOrchestrator()


def require_bot_auth(x_bot_auth: str = Header(default="")) -> None:
    """Constant-time check of the shared secret on every protected endpoint."""
    if not hmac.compare_digest(x_bot_auth or "", BOT_SHARED_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-Bot-Auth header",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the bot service."""
    logger.info("Bot service starting up... (API_URL=%s)", API_URL)
    await orchestrator.initialize()
    yield
    logger.info("Bot service shutting down...")
    await orchestrator.shutdown()


app = FastAPI(
    title="Vaktram Bot Service",
    description="Manages meeting bots that join calls, capture audio, and stream for transcription.",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class StartBotRequest(BaseModel):
    meeting_id: str = Field(..., description="Internal meeting record ID")
    meeting_url: str = Field(..., description="The meeting join link (Google Meet, Zoom, Teams)")
    platform: Optional[str] = Field(
        default=None,
        description="Platform identifier; auto-detected from URL when omitted",
    )
    bot_name: str = Field(default="Vaktram Notetaker", description="Display name for the bot")
    user_id: Optional[str] = Field(default=None, description="Owner user ID for audio upload callback")
    organization_id: Optional[str] = Field(default=None, description="Organization ID for storage path")


class StopBotRequest(BaseModel):
    meeting_id: str = Field(..., description="Internal meeting record ID")


class BotStatusResponse(BaseModel):
    meeting_id: str
    status: str
    platform: str
    uptime_seconds: float = 0.0
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    active_bots: int
    version: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health check."""
    return HealthResponse(
        status="healthy",
        active_bots=orchestrator.active_bot_count,
        version="0.1.0",
    )


@app.post(
    "/bots/start",
    response_model=BotStatusResponse,
    dependencies=[Depends(require_bot_auth)],
)
async def start_bot(request: StartBotRequest, background_tasks: BackgroundTasks):
    """Launch a bot into a meeting."""
    if orchestrator.has_bot(request.meeting_id):
        raise HTTPException(status_code=409, detail="Bot already active for this meeting")

    platform = request.platform or detect_platform(request.meeting_url)
    try:
        bot_info = await orchestrator.start_bot(
            meeting_id=request.meeting_id,
            meeting_url=request.meeting_url,
            platform=platform,
            bot_name=request.bot_name,
            user_id=request.user_id,
            organization_id=request.organization_id,
        )
        return BotStatusResponse(
            meeting_id=request.meeting_id,
            status=bot_info["status"],
            platform=platform,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to start bot for meeting %s", request.meeting_id)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post(
    "/bots/stop",
    response_model=BotStatusResponse,
    dependencies=[Depends(require_bot_auth)],
)
async def stop_bot(request: StopBotRequest):
    """Stop a running bot and finalize the recording."""
    if not orchestrator.has_bot(request.meeting_id):
        raise HTTPException(status_code=404, detail="No active bot for this meeting")

    try:
        result = await orchestrator.stop_bot(request.meeting_id)
        return BotStatusResponse(
            meeting_id=request.meeting_id,
            status=result["status"],
            platform=result.get("platform", "unknown"),
            uptime_seconds=result.get("uptime_seconds", 0.0),
        )
    except Exception as exc:
        logger.exception("Failed to stop bot for meeting %s", request.meeting_id)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get(
    "/bots/{meeting_id}",
    response_model=BotStatusResponse,
    dependencies=[Depends(require_bot_auth)],
)
async def get_bot_status(meeting_id: str):
    """Get the current status of a bot."""
    status = orchestrator.get_bot_status(meeting_id)
    if status is None:
        raise HTTPException(status_code=404, detail="No bot found for this meeting")
    return status


@app.get("/bots", dependencies=[Depends(require_bot_auth)])
async def list_bots():
    """List all active bots."""
    return {"bots": orchestrator.list_bots()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "bot.main:app",
        host="0.0.0.0",
        port=int(os.getenv("BOT_SERVICE_PORT", "8100")),
        reload=os.getenv("ENV", "development") == "development",
    )
