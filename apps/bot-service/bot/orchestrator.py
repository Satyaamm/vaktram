"""
BotOrchestrator - manages the lifecycle of multiple concurrent meeting bots.
Each bot runs as an asyncio task within this process.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from bot.audio.processor import concatenate_chunks, wav_to_flac
from bot.audio.uploader import upload_audio_file
from bot.platforms.base import BaseMeetingBot, BotState
from bot.platforms.google_meet import GoogleMeetBot

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://api:8000")

PLATFORM_REGISTRY: Dict[str, type] = {
    "google_meet": GoogleMeetBot,
}


class ManagedBot:
    """Wrapper around a platform bot that tracks metadata and the running task."""

    def __init__(
        self,
        meeting_id: str,
        bot: BaseMeetingBot,
        platform: str,
        callback_url: Optional[str] = None,
        organization_id: Optional[str] = None,
    ):
        self.meeting_id = meeting_id
        self.bot = bot
        self.platform = platform
        self.callback_url = callback_url
        self.organization_id = organization_id
        self.task: Optional[asyncio.Task] = None
        self.started_at: float = time.time()
        self.error: Optional[str] = None

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.started_at

    def to_status_dict(self) -> Dict[str, Any]:
        return {
            "meeting_id": self.meeting_id,
            "status": self.bot.state.value,
            "platform": self.platform,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "error": self.error,
        }


class BotOrchestrator:
    """Manages creation, monitoring, and teardown of meeting bots."""

    def __init__(self, max_concurrent: int = 10):
        self._bots: Dict[str, ManagedBot] = {}
        self._max_concurrent = max_concurrent
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Called once on service startup."""
        logger.info("BotOrchestrator initialized (max_concurrent=%d)", self._max_concurrent)

    async def shutdown(self) -> None:
        """Gracefully stop all running bots."""
        logger.info("Shutting down %d active bots...", len(self._bots))
        tasks = []
        for meeting_id in list(self._bots.keys()):
            tasks.append(self.stop_bot(meeting_id))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All bots stopped.")

    @property
    def active_bot_count(self) -> int:
        return len(self._bots)

    def has_bot(self, meeting_id: str) -> bool:
        return meeting_id in self._bots

    def get_bot_status(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        managed = self._bots.get(meeting_id)
        if managed is None:
            return None
        return managed.to_status_dict()

    def list_bots(self) -> List[Dict[str, Any]]:
        return [m.to_status_dict() for m in self._bots.values()]

    async def start_bot(
        self,
        meeting_id: str,
        meeting_url: str,
        platform: str,
        bot_name: str = "Vaktram Notetaker",
        callback_url: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Instantiate and launch a meeting bot."""
        async with self._lock:
            if len(self._bots) >= self._max_concurrent:
                raise ValueError(
                    f"Max concurrent bots reached ({self._max_concurrent})"
                )

            bot_cls = PLATFORM_REGISTRY.get(platform)
            if bot_cls is None:
                raise ValueError(f"Unsupported platform: {platform}")

            bot = bot_cls(
                meeting_url=meeting_url,
                bot_name=bot_name,
                meeting_id=meeting_id,
            )

            managed = ManagedBot(
                meeting_id=meeting_id,
                bot=bot,
                platform=platform,
                callback_url=callback_url,
                organization_id=organization_id,
            )

            # Launch the bot lifecycle as a background task
            managed.task = asyncio.create_task(
                self._run_bot(managed),
                name=f"bot-{meeting_id}",
            )

            self._bots[meeting_id] = managed
            logger.info("Bot started for meeting %s on %s", meeting_id, platform)
            return {"status": bot.state.value}

    async def stop_bot(self, meeting_id: str) -> Dict[str, Any]:
        """Stop a running bot and clean up resources."""
        async with self._lock:
            managed = self._bots.pop(meeting_id, None)

        if managed is None:
            raise ValueError(f"No bot found for meeting {meeting_id}")

        result = managed.to_status_dict()

        try:
            await managed.bot.leave()
        except Exception:
            logger.exception("Error leaving meeting %s", meeting_id)

        if managed.task and not managed.task.done():
            managed.task.cancel()
            try:
                await managed.task
            except asyncio.CancelledError:
                pass

        result["status"] = "stopped"
        logger.info("Bot stopped for meeting %s", meeting_id)
        return result

    async def _run_bot(self, managed: ManagedBot) -> None:
        """Main bot lifecycle: join -> record -> leave -> process & upload audio."""
        # Capture audio output_dir before stop_recording clears the reference
        audio_output_dir: Optional[str] = None
        try:
            await managed.bot.join()
            await managed.bot.start_recording()

            # Grab the audio capture output directory while it's still available
            if hasattr(managed.bot, "_audio_capture") and managed.bot._audio_capture:
                audio_output_dir = str(managed.bot._audio_capture.output_dir)

            # Keep running until cancelled or the bot detects the meeting ended
            while managed.bot.state == BotState.RECORDING:
                await asyncio.sleep(2)

        except asyncio.CancelledError:
            logger.info("Bot task cancelled for meeting %s", managed.meeting_id)
        except Exception as exc:
            managed.error = str(exc)
            logger.exception("Bot error for meeting %s", managed.meeting_id)
        finally:
            # Grab output dir one more time in case it wasn't captured above
            if audio_output_dir is None and hasattr(managed.bot, "_audio_capture") and managed.bot._audio_capture:
                audio_output_dir = str(managed.bot._audio_capture.output_dir)

            try:
                await managed.bot.stop_recording()
                await managed.bot.leave()
            except Exception:
                logger.exception("Error during bot cleanup for meeting %s", managed.meeting_id)

            # Process and upload audio, then notify the API
            await self._process_and_upload_audio(managed, audio_output_dir)

            # Remove from active bots if still present
            async with self._lock:
                self._bots.pop(managed.meeting_id, None)

    async def _process_and_upload_audio(
        self,
        managed: ManagedBot,
        audio_output_dir: Optional[str],
    ) -> None:
        """Concatenate audio chunks, convert to FLAC, upload, and notify API."""
        meeting_id = managed.meeting_id
        try:
            if audio_output_dir is None:
                # Fall back to the default path used by AudioCapture
                audio_output_dir = f"/tmp/vaktram/audio/{meeting_id}"

            chunk_dir = Path(audio_output_dir)
            if not chunk_dir.exists() or not list(chunk_dir.glob("chunk_*.pcm")):
                logger.warning(
                    "[%s] No audio chunks found in %s, skipping upload",
                    meeting_id,
                    audio_output_dir,
                )
                return

            # Step 1: Concatenate PCM chunks into a single WAV
            wav_path = str(chunk_dir / "recording.wav")
            await concatenate_chunks(
                chunk_dir=audio_output_dir,
                output_path=wav_path,
            )

            # Step 2: Convert WAV to FLAC for efficient storage
            flac_path = await wav_to_flac(wav_path)

            # Step 3: Upload FLAC to Supabase Storage
            organization_id = managed.organization_id or "default"
            storage_key = await upload_audio_file(
                local_path=flac_path,
                meeting_id=meeting_id,
                organization_id=organization_id,
                content_type="audio/flac",
            )

            logger.info(
                "[%s] Audio uploaded to storage: %s",
                meeting_id,
                storage_key,
            )

            # Step 4: Notify API that audio is ready for transcription
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/internal/meetings/{meeting_id}/audio-ready",
                    json={"storage_key": storage_key},
                    timeout=10.0,
                )
                resp.raise_for_status()

            logger.info("[%s] API notified: audio-ready", meeting_id)

        except Exception as exc:
            logger.exception(
                "[%s] Failed to process/upload audio", meeting_id
            )
            # Notify API about the pipeline error
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{API_URL}/internal/meetings/{meeting_id}/pipeline-error",
                        json={
                            "stage": "audio_upload",
                            "error": str(exc),
                        },
                        timeout=10.0,
                    )
            except Exception:
                logger.exception(
                    "[%s] Failed to notify API about pipeline error",
                    meeting_id,
                )
