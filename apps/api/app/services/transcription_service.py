"""Transcription service using Groq Whisper API + optional pyannote diarization."""

from __future__ import annotations

import logging
import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.transcript import TranscriptSegment

logger = logging.getLogger(__name__)
settings = get_settings()

GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str,
    meeting_id: uuid.UUID,
    db: AsyncSession,
    diarization_segments: list[dict] | None = None,
) -> int:
    """Transcribe audio using Groq Whisper API and save segments to DB.

    Args:
        audio_bytes: Raw audio file bytes
        filename: Original filename for content-type detection
        meeting_id: Meeting UUID
        db: Database session
        diarization_segments: Optional list of {"start": float, "end": float, "speaker": str}
            from pyannote diarization. If provided, speakers are assigned to segments.

    Returns the number of segments created.
    """
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    # Call Groq Whisper API
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            GROQ_TRANSCRIPTION_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            files={"file": (filename, audio_bytes)},
            data={
                "model": "whisper-large-v3-turbo",
                "response_format": "verbose_json",
                "language": "en",
            },
        )
        resp.raise_for_status()
        result = resp.json()

    # Parse segments from Groq response
    segments = result.get("segments", [])
    if not segments:
        full_text = result.get("text", "").strip()
        if full_text:
            segments = [{"start": 0.0, "end": result.get("duration", 0.0), "text": full_text}]

    # Assign speakers if diarization data is available
    db_segments = []
    for i, seg in enumerate(segments):
        speaker = "Speaker"
        if diarization_segments:
            speaker = _assign_speaker(
                seg.get("start", 0.0),
                seg.get("end", 0.0),
                diarization_segments,
            )

        db_seg = TranscriptSegment(
            meeting_id=meeting_id,
            speaker_name=speaker,
            content=seg.get("text", "").strip(),
            start_time=seg.get("start", 0.0),
            end_time=seg.get("end", 0.0),
            sequence_number=i,
            confidence=seg.get("avg_logprob", None),
            language=result.get("language", "en"),
        )
        db.add(db_seg)
        db_segments.append(db_seg)

    await db.flush()
    logger.info("Transcribed meeting %s: %d segments", meeting_id, len(db_segments))
    return len(db_segments)


def _assign_speaker(
    seg_start: float,
    seg_end: float,
    diarization_segments: list[dict],
) -> str:
    """Assign a speaker to a transcript segment based on max overlap with diarization."""
    best_speaker = "Speaker"
    best_overlap = 0.0

    for dseg in diarization_segments:
        overlap_start = max(seg_start, dseg["start"])
        overlap_end = min(seg_end, dseg["end"])
        overlap = max(0.0, overlap_end - overlap_start)

        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = dseg["speaker"]

    return best_speaker
