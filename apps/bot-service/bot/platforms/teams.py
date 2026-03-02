"""
Microsoft Teams Meeting Bot - Phase 3 stub.
Will use the Bot Framework SDK or Playwright-based approach.
"""

import logging

from bot.platforms.base import BaseMeetingBot, BotState

logger = logging.getLogger(__name__)


class TeamsBot(BaseMeetingBot):
    """Microsoft Teams meeting bot (Phase 3 - not yet implemented)."""

    async def join(self) -> None:
        self.state = BotState.ERROR
        raise NotImplementedError(
            "Teams bot is planned for Phase 3. "
            "Will integrate with Microsoft Bot Framework or "
            "Playwright-based browser automation for Teams meetings."
        )

    async def leave(self) -> None:
        logger.info("[%s] Teams leave (stub)", self.meeting_id)
        self.state = BotState.LEFT

    async def start_recording(self) -> None:
        raise NotImplementedError("Teams recording not yet implemented")

    async def stop_recording(self) -> None:
        pass

    async def is_meeting_active(self) -> bool:
        return False

    async def participant_count(self) -> int:
        return 0
