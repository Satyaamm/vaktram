"""Health check endpoints.

Both `/health` (liveness) and `/healthz` (readiness) accept GET *and* HEAD.
HEAD support matters because most external monitors (UptimeRobot, K8s probes,
AWS / GCP load balancers) default to HEAD for cheaper checks; without it
they'd see 405 Method Not Allowed and report the API as down.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

router = APIRouter(tags=["health"])


@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Liveness — returns 200 if the process is alive."""
    return {"status": "ok"}


@router.api_route("/healthz", methods=["GET", "HEAD"])
async def deep_health_check(db: AsyncSession = Depends(get_db)):
    """Readiness — also confirms database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
    }
