"""
Zoom Meeting Bot - Phase 2 stub.
Will use Zoom's Meeting SDK or Web SDK for joining meetings.
"""

import logging

from bot.platforms.base import BaseMeetingBot, BotState

logger = logging.getLogger(__name__)


class ZoomBot(BaseMeetingBot):
    """Zoom meeting bot (Phase 2 - not yet implemented)."""

    async def join(self) -> None:
        self.state = BotState.ERROR
        raise NotImplementedError(
            "Zoom bot is planned for Phase 2. "
            "Will integrate with Zoom Meeting SDK for native join, "
            "audio capture, and real-time streaming."
        )

    async def leave(self) -> None:
        logger.info("[%s] Zoom leave (stub)", self.meeting_id)
        self.state = BotState.LEFT

    async def start_recording(self) -> None:
        raise NotImplementedError("Zoom recording not yet implemented")

    async def stop_recording(self) -> None:
        pass

    async def is_meeting_active(self) -> bool:
        return False

    async def participant_count(self) -> int:
        return 0
