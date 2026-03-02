"""Health check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic liveness probe."""
    return {"status": "ok"}


@router.get("/healthz")
async def deep_health_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe -- verifies database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
    }
