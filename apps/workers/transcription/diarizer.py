"""
Speaker diarization using pyannote.audio.
Assigns speaker labels to time segments of the audio.
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

import torch

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN", "")


@dataclass
class DiarizationSegment:
    """A speaker turn with start/end times."""
    start: float
    end: float
    speaker: str


class Diarizer:
    """Wraps pyannote.audio speaker diarization pipeline."""

    def __init__(
        self,
        model_name: str = "pyannote/speaker-diarization-3.1",
        device: str = "auto",
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
    ):
        self.model_name = model_name
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers
        self._pipeline = None

        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

    def initialize(self) -> None:
        """Load the pyannote diarization pipeline."""
        from pyannote.audio import Pipeline

        logger.info("Loading diarization pipeline: %s", self.model_name)

        if not HF_TOKEN:
            logger.warning(
                "HF_TOKEN not set. pyannote models require a Hugging Face token "
                "with access to pyannote/speaker-diarization-3.1"
            )

        self._pipeline = Pipeline.from_pretrained(
            self.model_name,
            use_auth_token=HF_TOKEN or None,
        )
        self._pipeline.to(self.device)
        logger.info("Diarization pipeline loaded on %s", self.device)

    def diarize(self, audio_path: str) -> List[DiarizationSegment]:
        """
        Run speaker diarization on an audio file.

        Args:
            audio_path: Path to the audio file (WAV format recommended)

        Returns:
            List of DiarizationSegment with speaker labels and timestamps
        """
        if self._pipeline is None:
            raise RuntimeError("Diarizer not initialized. Call initialize() first.")

        params = {}
        if self.min_speakers is not None:
            params["min_speakers"] = self.min_speakers
        if self.max_speakers is not None:
            params["max_speakers"] = self.max_speakers

        logger.info("Running diarization on %s", audio_path)
        diarization = self._pipeline(audio_path, **params)

        segments: List[DiarizationSegment] = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append(
                DiarizationSegment(
                    start=round(turn.start, 3),
                    end=round(turn.end, 3),
                    speaker=speaker,
                )
            )

        logger.info(
            "Diarization complete: %d turns, %d speakers",
            len(segments),
            len(set(s.speaker for s in segments)),
        )
        return segments
