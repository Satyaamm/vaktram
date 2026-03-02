"""
Abstract base class for all meeting platform bots.
Each platform (Google Meet, Zoom, Teams) implements this interface.
"""

import enum
from abc import ABC, abstractmethod
from typing import Optional


class BotState(enum.Enum):
    IDLE = "idle"
    JOINING = "joining"
    IN_MEETING = "in_meeting"
    RECORDING = "recording"
    LEAVING = "leaving"
    LEFT = "left"
    ERROR = "error"


class BaseMeetingBot(ABC):
    """Interface every platform bot must implement."""

    def __init__(
        self,
        meeting_url: str,
        bot_name: str,
        meeting_id: str,
    ):
        self.meeting_url = meeting_url
        self.bot_name = bot_name
        self.meeting_id = meeting_id
        self.state: BotState = BotState.IDLE
        self._error: Optional[str] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def join(self) -> None:
        """Navigate to the meeting and join as a participant."""
        ...

    @abstractmethod
    async def leave(self) -> None:
        """Leave the meeting and close the browser context."""
        ...

    @abstractmethod
    async def start_recording(self) -> None:
        """Begin capturing audio from the meeting."""
        ...

    @abstractmethod
    async def stop_recording(self) -> None:
        """Stop capturing audio and flush buffers."""
        ...

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @abstractmethod
    async def is_meeting_active(self) -> bool:
        """Return True if the meeting is still in progress."""
        ...

    @abstractmethod
    async def participant_count(self) -> int:
        """Return the current number of participants."""
        ...

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def set_error(self, message: str) -> None:
        self._error = message
        self.state = BotState.ERROR

    @property
    def error_message(self) -> Optional[str]:
        return self._error
