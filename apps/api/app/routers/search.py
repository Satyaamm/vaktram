"""Semantic search endpoints. Vector retrieval uses the caller's BYOM key."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.ai_config import UserAIConfig
from app.models.team import UserProfile
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


async def _user_ai_config(db: AsyncSession, user_id) -> UserAIConfig | None:
    rows = await db.execute(
        select(UserAIConfig)
        .where(UserAIConfig.user_id == user_id, UserAIConfig.is_active.is_(True))
        .order_by(UserAIConfig.is_default.desc(), UserAIConfig.created_at.desc())
        .limit(1)
    )
    return rows.scalar_one_or_none()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    meeting_id: str
    meeting_title: str
    segment_id: str
    content: str
    speaker_name: str
    score: float
    start_time: float
    end_time: float


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    query: str
    total: int


@router.post("", response_model=SearchResponse)
async def semantic_search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Perform semantic search across meeting transcripts.

    Vector retrieval uses the caller's BYOM provider key when available; FTS
    works regardless.
    """
    service = SearchService(db)
    ai_config = await _user_ai_config(db, user.id)
    results = await service.search(
        query=payload.query,
        user_id=user.id,
        organization_id=user.organization_id,
        ai_config=ai_config,
        top_k=payload.top_k,
    )
    return SearchResponse(
        results=results,
        query=payload.query,
        total=len(results),
    )
