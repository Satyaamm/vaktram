"""
Transcription Worker - polls for meetings with status 'transcribing',
downloads audio from Supabase Storage, processes through Faster-Whisper
and pyannote diarization, then writes results back and notifies the API.
"""

import asyncio
import logging
import os
import signal
import sys
import tempfile
from datetime import datetime, timezone

import httpx
from supabase import create_client, Client

from processor import TranscriptionProcessor

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("transcription-worker")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))
STORAGE_BUCKET = os.getenv("AUDIO_STORAGE_BUCKET", "meeting-recordings")
API_URL = os.getenv("API_URL", "http://api:8000")
BOT_SHARED_SECRET = os.getenv("BOT_SHARED_SECRET", "")
INTERNAL_HEADERS = {"X-Bot-Auth": BOT_SHARED_SECRET} if BOT_SHARED_SECRET else {}

_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    logger.info("Received signal %s, shutting down gracefully...", signum)
    _shutdown = True


def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


async def poll_for_jobs(processor: TranscriptionProcessor) -> None:
    """Main polling loop: find meetings in 'transcribing' status, process them."""
    supabase = get_supabase()
    meeting_id = None

    while not _shutdown:
        try:
            # Poll for meetings with status = 'transcribing'
            result = (
                supabase.table("meetings")
                .select("id, audio_url, created_by, organization_id")
                .eq("status", "transcribing")
                .order("updated_at", desc=False)
                .limit(1)
                .execute()
            )

            if not result.data:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            meeting = result.data[0]
            meeting_id = meeting["id"]
            audio_storage_path = meeting["audio_url"]

            if not audio_storage_path:
                logger.warning(
                    "Meeting %s has status 'transcribing' but no audio_url, skipping",
                    meeting_id,
                )
                await asyncio.sleep(POLL_INTERVAL)
                continue

            logger.info("Processing transcription for meeting %s", meeting_id)

            # Download audio file from Supabase Storage
            with tempfile.NamedTemporaryFile(suffix=".flac", delete=False) as tmp:
                audio_data = supabase.storage.from_(STORAGE_BUCKET).download(
                    audio_storage_path
                )
                tmp.write(audio_data)
                local_audio_path = tmp.name

            try:
                # Run transcription + diarization
                result_data = await processor.process(local_audio_path)

                # Write transcript segments to database
                segments = result_data["segments"]
                for segment in segments:
                    supabase.table("transcript_segments").insert({
                        "meeting_id": meeting_id,
                        "speaker_label": segment["speaker"],
                        "start_time": segment["start"],
                        "end_time": segment["end"],
                        "text": segment["text"],
                        "confidence": segment.get("confidence", 0.0),
                    }).execute()

                # Notify API that transcription is complete
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{API_URL}/internal/meetings/{meeting_id}/transcription-complete",
                        headers=INTERNAL_HEADERS,
                        json={"segment_count": len(segments)},
                        timeout=10.0,
                    )
                    resp.raise_for_status()

                logger.info(
                    "Transcription complete for meeting %s: %d segments",
                    meeting_id,
                    len(segments),
                )

            finally:
                # Clean up temp file
                if os.path.exists(local_audio_path):
                    os.unlink(local_audio_path)

            # Reset meeting_id so error handler doesn't misfire
            meeting_id = None

        except Exception as exc:
            logger.exception("Error in transcription polling loop")
            # Notify API about the pipeline error if we have a meeting_id
            if meeting_id:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{API_URL}/internal/meetings/{meeting_id}/pipeline-error",
                            headers=INTERNAL_HEADERS,
                            json={
                                "stage": "transcription",
                                "error": str(exc),
                            },
                            timeout=10.0,
                        )
                except Exception:
                    logger.exception("Failed to notify API about pipeline error")
                meeting_id = None

            await asyncio.sleep(POLL_INTERVAL)


async def main() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    whisper_model = os.getenv("WHISPER_MODEL", "large-v3")
    device = os.getenv("COMPUTE_DEVICE", "auto")

    logger.info("Starting transcription worker (model=%s, device=%s)", whisper_model, device)

    processor = TranscriptionProcessor(
        whisper_model_size=whisper_model,
        device=device,
    )
    await processor.initialize()

    logger.info("Worker ready. Polling every %ds...", POLL_INTERVAL)
    await poll_for_jobs(processor)

    logger.info("Worker shut down.")


if __name__ == "__main__":
    asyncio.run(main())
