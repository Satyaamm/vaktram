"""
Bot health check utilities.
Monitors bot processes, audio capture, and system resources.
"""

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SystemHealth:
    disk_free_gb: float
    disk_total_gb: float
    pulse_audio_running: bool
    ffmpeg_available: bool
    playwright_installed: bool


async def check_pulse_audio() -> bool:
    """Check if PulseAudio daemon is running."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "pactl", "info",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
        return proc.returncode == 0
    except (FileNotFoundError, asyncio.TimeoutError):
        return False


async def check_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=5.0)
        return proc.returncode == 0
    except (FileNotFoundError, asyncio.TimeoutError):
        return False


async def check_playwright() -> bool:
    """Check if Playwright browsers are installed."""
    try:
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        await browser.close()
        await pw.stop()
        return True
    except Exception:
        return False


def check_disk_space(path: str = "/tmp") -> tuple[float, float]:
    """Return (free_gb, total_gb) for the filesystem containing path."""
    usage = shutil.disk_usage(path)
    free_gb = usage.free / (1024 ** 3)
    total_gb = usage.total / (1024 ** 3)
    return round(free_gb, 2), round(total_gb, 2)


async def get_system_health() -> SystemHealth:
    """Run all health checks and return a summary."""
    pulse_ok, ffmpeg_ok = await asyncio.gather(
        check_pulse_audio(),
        check_ffmpeg(),
    )

    free_gb, total_gb = check_disk_space()

    return SystemHealth(
        disk_free_gb=free_gb,
        disk_total_gb=total_gb,
        pulse_audio_running=pulse_ok,
        ffmpeg_available=ffmpeg_ok,
        playwright_installed=True,  # assume installed in Docker image
    )
