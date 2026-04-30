"""Hybrid search across user/org meetings.

BYOM-pure: vector retrieval uses the caller's `UserAIConfig`. When no config
is provided (or the provider doesn't support embeddings), we silently fall
back to Postgres full-text search. The endpoint never errors just because
embeddings aren't available.

Strategy: run vector cosine similarity (Python-side over a candidate set) and
Postgres FTS in parallel, then merge via Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import UserAIConfig
from app.models.meeting import Meeting
from app.models.team import MeetingEmbedding
from app.models.transcript import TranscriptSegment
from app.services.embedding_service import ProviderUnsupported, embed_texts

logger = logging.getLogger(__name__)
RRF_K = 60  # standard RRF damping constant


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        query: str,
        user_id: uuid.UUID,
        organization_id: uuid.UUID | None = None,
        ai_config: UserAIConfig | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Run hybrid (vector + FTS) search and return ranked hits."""
        fts_hits = await self._fts(query, user_id, organization_id, top_k)
        vec_hits: list[dict] = []
        if ai_config is not None:
            try:
                vec_hits = await self._vector(
                    query, user_id, organization_id, top_k, ai_config
                )
            except ProviderUnsupported as e:
                logger.info("Vector search unavailable: %s", e)
            except Exception as e:  # noqa: BLE001
                logger.warning("Vector search failed, falling back to FTS: %s", e)
        return self._rrf_merge(fts_hits, vec_hits, top_k)

    # ─── individual retrievers ──────────────────────────────────────────

    async def _fts(
        self,
        query: str,
        user_id: uuid.UUID,
        organization_id: uuid.UUID | None,
        top_k: int,
    ) -> list[dict]:
        # plainto_tsquery is forgiving of bad input. Use english config.
        sql = text(
            """
            SELECT
                ts.id          AS segment_id,
                ts.meeting_id  AS meeting_id,
                ts.content     AS content,
                ts.speaker_name,
                ts.start_time,
                ts.end_time,
                m.title        AS meeting_title,
                ts_rank(to_tsvector('english', ts.content),
                        plainto_tsquery('english', :q)) AS rank
            FROM vaktram.transcript_segments ts
            JOIN vaktram.meetings m ON m.id = ts.meeting_id
            WHERE (m.user_id = :uid OR m.organization_id = :oid)
              AND to_tsvector('english', ts.content)
                  @@ plainto_tsquery('english', :q)
            ORDER BY rank DESC
            LIMIT :k
            """
        )
        rows = (
            await self.db.execute(
                sql,
                {"q": query, "uid": user_id, "oid": organization_id, "k": top_k * 3},
            )
        ).mappings().all()
        return [dict(r) for r in rows]

    async def _vector(
        self,
        query: str,
        user_id: uuid.UUID,
        organization_id: uuid.UUID | None,
        top_k: int,
        ai_config: UserAIConfig,
    ) -> list[dict]:
        [vector] = await embed_texts([query], ai_config=ai_config)
        # Stored in JSONB today; cast to vector via text concat is not portable,
        # so we compute cosine similarity in Python over a candidate set
        # bounded by the meeting filter. Once pgvector column lands we swap to
        # `embedding <=> :v::vector` with an IVFFlat index.
        result = await self.db.execute(
            select(
                MeetingEmbedding.id,
                MeetingEmbedding.segment_id,
                MeetingEmbedding.meeting_id,
                MeetingEmbedding.content,
                MeetingEmbedding.embedding,
                Meeting.title,
            )
            .join(Meeting, Meeting.id == MeetingEmbedding.meeting_id)
            .where(
                (Meeting.user_id == user_id)
                | (Meeting.organization_id == organization_id)
            )
            .where(MeetingEmbedding.embedding.is_not(None))
            .limit(2000)  # bounded candidate set
        )
        rows = result.all()
        scored: list[dict] = []
        qnorm = _norm(vector)
        for r in rows:
            v = (r.embedding or {}).get("vector") if isinstance(r.embedding, dict) else None
            if not v:
                continue
            sim = _cosine(vector, v, qnorm)
            scored.append(
                {
                    "segment_id": r.segment_id,
                    "meeting_id": r.meeting_id,
                    "content": r.content,
                    "speaker_name": None,
                    "start_time": None,
                    "end_time": None,
                    "meeting_title": r.title,
                    "rank": sim,
                }
            )
        scored.sort(key=lambda x: x["rank"], reverse=True)
        return scored[: top_k * 3]

    # ─── fusion ─────────────────────────────────────────────────────────

    @staticmethod
    def _rrf_merge(
        fts: list[dict], vec: list[dict], top_k: int
    ) -> list[dict[str, Any]]:
        scores: dict[tuple, dict] = {}
        for i, hit in enumerate(fts):
            key = (hit.get("segment_id"), hit.get("meeting_id"))
            scores.setdefault(key, {"hit": hit, "score": 0.0})
            scores[key]["score"] += 1.0 / (RRF_K + i + 1)
        for i, hit in enumerate(vec):
            key = (hit.get("segment_id"), hit.get("meeting_id"))
            scores.setdefault(key, {"hit": hit, "score": 0.0})
            scores[key]["score"] += 1.0 / (RRF_K + i + 1)
        merged = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        return [
            {
                "segment_id": str(s["hit"].get("segment_id")) if s["hit"].get("segment_id") else None,
                "meeting_id": str(s["hit"]["meeting_id"]),
                "meeting_title": s["hit"].get("meeting_title"),
                "content": s["hit"].get("content"),
                "speaker_name": s["hit"].get("speaker_name"),
                "start_time": s["hit"].get("start_time"),
                "end_time": s["hit"].get("end_time"),
                "score": round(s["score"], 6),
            }
            for s in merged[:top_k]
        ]

    # legacy hook kept for callers — accepts ai_config so embeddings are BYOM
    async def generate_and_store_embedding(
        self,
        meeting_id: uuid.UUID,
        segment_id: uuid.UUID,
        content: str,
        ai_config: UserAIConfig | None = None,
    ) -> None:
        from app.services.embedding_service import index_segments

        await index_segments(
            self.db,
            meeting_id=meeting_id,
            segments=[(segment_id, content)],
            ai_config=ai_config,
        )


def _norm(v: list[float]) -> float:
    return sum(x * x for x in v) ** 0.5


def _cosine(a: list[float], b: list[float], anorm: float | None = None) -> float:
    bnorm = _norm(b)
    if not bnorm:
        return 0.0
    anorm = anorm if anorm is not None else _norm(a)
    if not anorm:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    return dot / (anorm * bnorm)
