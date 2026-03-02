"""
Audio capture using PulseAudio virtual sink.
Captures system audio output from the browser running inside the container,
writes raw PCM chunks to disk, and signals availability for processing.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# PulseAudio monitor source for the virtual sink
PULSE_MONITOR = os.getenv("PULSE_MONITOR_SOURCE", "vaktram_sink.monitor")
SAMPLE_RATE = 16_000
CHANNELS = 1
FORMAT = "s16le"  # signed 16-bit little-endian PCM
CHUNK_DURATION_SEC = 30  # each chunk is 30 seconds


class AudioCapture:
    """
    Captures audio from PulseAudio using parec (PulseAudio recording tool).
    Writes PCM chunks to a local directory for downstream processing.
    """

    def __init__(self, meeting_id: str, output_dir: Optional[str] = None):
        self.meeting_id = meeting_id
        self.output_dir = Path(output_dir or f"/tmp/vaktram/audio/{meeting_id}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._process: Optional[asyncio.subprocess.Process] = None
        self._running = False
        self._chunk_index = 0
        self._writer_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start capturing audio from PulseAudio monitor source."""
        if self._running:
            logger.warning("[%s] Audio capture already running", self.meeting_id)
            return

        logger.info("[%s] Starting audio capture from %s", self.meeting_id, PULSE_MONITOR)

        cmd = [
            "parec",
            "--device", PULSE_MONITOR,
            "--format", FORMAT,
            "--rate", str(SAMPLE_RATE),
            "--channels", str(CHANNELS),
            "--raw",
        ]

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._running = True
        self._writer_task = asyncio.create_task(self._write_chunks())
        logger.info("[%s] Audio capture started (PID=%s)", self.meeting_id, self._process.pid)

    async def stop(self) -> None:
        """Stop audio capture and finalize the last chunk."""
        if not self._running:
            return

        self._running = False

        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
            except ProcessLookupError:
                pass

        if self._writer_task:
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass

        logger.info(
            "[%s] Audio capture stopped. %d chunks written to %s",
            self.meeting_id,
            self._chunk_index,
            self.output_dir,
        )

    async def _write_chunks(self) -> None:
        """Read from parec stdout and split into fixed-duration chunks."""
        bytes_per_second = SAMPLE_RATE * CHANNELS * 2  # 16-bit = 2 bytes
        chunk_bytes = bytes_per_second * CHUNK_DURATION_SEC
        buffer = bytearray()

        try:
            while self._running and self._process and self._process.stdout:
                data = await self._process.stdout.read(4096)
                if not data:
                    break
                buffer.extend(data)

                while len(buffer) >= chunk_bytes:
                    chunk = bytes(buffer[:chunk_bytes])
                    del buffer[:chunk_bytes]
                    await self._save_chunk(chunk)

            # Flush remaining buffer
            if buffer:
                await self._save_chunk(bytes(buffer))

        except asyncio.CancelledError:
            if buffer:
                await self._save_chunk(bytes(buffer))
            raise

    async def _save_chunk(self, data: bytes) -> None:
        """Write a chunk to disk."""
        filename = f"chunk_{self._chunk_index:04d}.pcm"
        filepath = self.output_dir / filename
        filepath.write_bytes(data)
        logger.debug(
            "[%s] Saved chunk %s (%d bytes)",
            self.meeting_id,
            filename,
            len(data),
        )
        self._chunk_index += 1

    @property
    def chunk_count(self) -> int:
        return self._chunk_index

    @property
    def is_running(self) -> bool:
        return self._running
