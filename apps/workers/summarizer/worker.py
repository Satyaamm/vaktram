"""
Summarization Worker - polls for meetings with status 'summarizing',
fetches transcript segments, generates summaries using the user's
configured AI provider (BYOM) or a default LLM, computes embeddings,
and notifies the API on completion.
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime, timezone

import httpx
from supabase import create_client, Client

from summarizer import Summarizer
from embedder import Embedder

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("summarizer-worker")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))
API_URL = os.getenv("API_URL", "http://api:8000")
BOT_SHARED_SECRET = os.getenv("BOT_SHARED_SECRET", "")
INTERNAL_HEADERS = {"X-Bot-Auth": BOT_SHARED_SECRET} if BOT_SHARED_SECRET else {}

# Default LLM fallback configuration
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gemini-2.0-flash")
DEFAULT_LLM_API_KEY = os.getenv("DEFAULT_LLM_API_KEY", "")

# Encryption key for decrypting user-stored API keys
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    logger.info("Received signal %s, shutting down gracefully...", signum)
    _shutdown = True


def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def _decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt a user's stored API key using the service encryption key."""
    if not ENCRYPTION_KEY:
        logger.warning("ENCRYPTION_KEY not set, returning key as-is")
        return encrypted_key

    try:
        from cryptography.fernet import Fernet
        f = Fernet(ENCRYPTION_KEY.encode())
        return f.decrypt(encrypted_key.encode()).decode()
    except Exception:
        logger.exception("Failed to decrypt API key, returning as-is")
        return encrypted_key


def _get_user_ai_config(supabase: Client, user_id: str) -> dict | None:
    """Look up the user's AI configuration from user_ai_configs table."""
    try:
        result = (
            supabase.table("user_ai_configs")
            .select("provider, model, api_key_encrypted")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
    except Exception:
        logger.exception("Failed to fetch user AI config for user %s", user_id)
    return None


async def poll_for_jobs(default_summarizer: Summarizer, embedder: Embedder) -> None:
    """Main polling loop: find meetings in 'summarizing' status and process them."""
    supabase = get_supabase()
    meeting_id = None

    while not _shutdown:
        try:
            # Poll for meetings with status = 'summarizing'
            result = (
                supabase.table("meetings")
                .select("id, created_by, organization_id")
                .eq("status", "summarizing")
                .order("updated_at", desc=False)
                .limit(1)
                .execute()
            )

            if not result.data:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            meeting = result.data[0]
            meeting_id = meeting["id"]
            created_by = meeting["created_by"]

            logger.info("Processing summarization for meeting %s", meeting_id)

            # Fetch transcript segments for this meeting
            transcript_result = (
                supabase.table("transcript_segments")
                .select("*")
                .eq("meeting_id", meeting_id)
                .order("start_time", desc=False)
                .execute()
            )

            segments = transcript_result.data
            if not segments:
                logger.warning("No transcript segments for meeting %s", meeting_id)
                # Notify API about error
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{API_URL}/internal/meetings/{meeting_id}/pipeline-error",
                        headers=INTERNAL_HEADERS,
                        json={
                            "stage": "summarization",
                            "error": "No transcript segments found",
                        },
                        timeout=10.0,
                    )
                meeting_id = None
                continue

            # Build full transcript text
            transcript_text = "\n".join(
                f"[{seg['speaker_label']}] ({seg['start_time']:.1f}s - {seg['end_time']:.1f}s): {seg['text']}"
                for seg in segments
            )

            # Determine which summarizer to use: user's BYOM config or default
            summarizer = default_summarizer
            user_config = _get_user_ai_config(supabase, created_by)

            if user_config:
                try:
                    api_key = _decrypt_api_key(user_config["api_key_encrypted"])
                    summarizer = Summarizer(
                        provider=user_config["provider"],
                        model=user_config["model"],
                        api_key=api_key,
                    )
                    logger.info(
                        "Using user BYOM config for meeting %s: %s/%s",
                        meeting_id,
                        user_config["provider"],
                        user_config["model"],
                    )
                except Exception:
                    logger.exception(
                        "Failed to initialize user summarizer for meeting %s, falling back to default",
                        meeting_id,
                    )
                    summarizer = default_summarizer

            # Generate all summaries
            summary_result = await summarizer.generate_all(transcript_text)

            # Store summary
            supabase.table("meeting_summaries").upsert({
                "meeting_id": meeting_id,
                "summary": summary_result["summary"],
                "action_items": summary_result["action_items"],
                "decisions": summary_result["decisions"],
                "follow_ups": summary_result["follow_ups"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }).execute()

            # Generate and store embeddings for semantic search
            chunks = _chunk_transcript(transcript_text, chunk_size=500)
            for i, chunk in enumerate(chunks):
                embedding = embedder.embed(chunk)
                supabase.table("transcript_embeddings").insert({
                    "meeting_id": meeting_id,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "embedding": embedding,
                }).execute()

            # Also embed the summary for search
            summary_embedding = embedder.embed(summary_result["summary"])
            supabase.table("transcript_embeddings").insert({
                "meeting_id": meeting_id,
                "chunk_index": -1,
                "chunk_text": summary_result["summary"],
                "embedding": summary_embedding,
                "is_summary": True,
            }).execute()

            # Notify API that summarization is complete
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/internal/meetings/{meeting_id}/summarization-complete",
                    headers=INTERNAL_HEADERS,
                    json={"embedding_chunks": len(chunks) + 1},
                    timeout=10.0,
                )
                resp.raise_for_status()

            logger.info(
                "Summarization complete for meeting %s: %d embedding chunks",
                meeting_id,
                len(chunks) + 1,
            )

            # Reset meeting_id so error handler doesn't misfire
            meeting_id = None

        except Exception as exc:
            logger.exception("Error in summarization polling loop")
            # Notify API about the pipeline error if we have a meeting_id
            if meeting_id:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{API_URL}/internal/meetings/{meeting_id}/pipeline-error",
                            headers=INTERNAL_HEADERS,
                            json={
                                "stage": "summarization",
                                "error": str(exc),
                            },
                            timeout=10.0,
                        )
                except Exception:
                    logger.exception("Failed to notify API about pipeline error")
                meeting_id = None

            await asyncio.sleep(POLL_INTERVAL)


def _chunk_transcript(text: str, chunk_size: int = 500) -> list[str]:
    """Split transcript into overlapping chunks for embedding."""
    words = text.split()
    chunks = []
    overlap = chunk_size // 5  # 20% overlap

    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap

    return chunks


async def main() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("Starting summarization worker")

    # Initialize default summarizer with fallback LLM
    default_summarizer = Summarizer(
        provider=DEFAULT_LLM_PROVIDER,
        model=DEFAULT_LLM_MODEL,
        api_key=DEFAULT_LLM_API_KEY,
    )
    embedder = Embedder()
    embedder.initialize()

    logger.info("Worker ready. Polling every %ds...", POLL_INTERVAL)
    await poll_for_jobs(default_summarizer, embedder)

    logger.info("Worker shut down.")


if __name__ == "__main__":
    asyncio.run(main())
