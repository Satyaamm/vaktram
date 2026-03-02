"""Semantic search endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.team import UserProfile
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    meeting_id: str
    meeting_title: str
    segment_content: str
    speaker_name: str
    score: float
    start_time: float


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
    """Perform semantic search across meeting transcripts."""
    service = SearchService(db)
    results = await service.search(
        query=payload.query,
        user_id=user.id,
        top_k=payload.top_k,
    )
    return SearchResponse(
        results=results,
        query=payload.query,
        total=len(results),
    )
