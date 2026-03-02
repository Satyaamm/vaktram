"""Semantic search service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.team import MeetingEmbedding
from app.models.transcript import TranscriptSegment


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        query: str,
        user_id: uuid.UUID,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Perform semantic search across user's meeting transcripts.

        Currently uses keyword-based search as a fallback.
        When pgvector embeddings are populated, this will switch to
        cosine similarity on the meeting_embeddings table.
        """
        # Keyword fallback: full-text search on transcript_segments
        search_term = f"%{query}%"
        result = await self.db.execute(
            select(
                TranscriptSegment.id,
                TranscriptSegment.meeting_id,
                TranscriptSegment.content,
                TranscriptSegment.speaker_name,
                TranscriptSegment.start_time,
                Meeting.title.label("meeting_title"),
            )
            .join(Meeting, Meeting.id == TranscriptSegment.meeting_id)
            .where(Meeting.user_id == user_id)
            .where(TranscriptSegment.content.ilike(search_term))
            .order_by(TranscriptSegment.start_time)
            .limit(top_k)
        )
        rows = result.all()

        return [
            {
                "meeting_id": str(row.meeting_id),
                "meeting_title": row.meeting_title,
                "segment_content": row.content,
                "speaker_name": row.speaker_name,
                "score": 1.0,  # Placeholder score for keyword search
                "start_time": row.start_time,
            }
            for row in rows
        ]

    async def generate_and_store_embedding(
        self,
        meeting_id: uuid.UUID,
        segment_id: uuid.UUID,
        content: str,
    ) -> None:
        """Generate an embedding vector and store it.

        TODO: integrate with an embedding model (OpenAI, sentence-transformers).
        """
        # Placeholder -- will call embedding API and store as JSONB / pgvector
        embedding = MeetingEmbedding(
            meeting_id=meeting_id,
            segment_id=segment_id,
            content=content,
            embedding=None,
            embedding_model="pending",
        )
        self.db.add(embedding)
        await self.db.flush()
