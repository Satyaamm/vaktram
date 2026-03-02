"""
Faster-Whisper integration for speech-to-text transcription.
Uses CTranslate2 backend for efficient inference.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    """A single transcription segment with timing."""
    start: float
    end: float
    text: str
    confidence: float
    language: Optional[str] = None


class Transcriber:
    """Wraps Faster-Whisper for audio transcription."""

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "auto",
        compute_type: str = "auto",
        language: Optional[str] = None,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model: Optional[WhisperModel] = None

    def initialize(self) -> None:
        """Load the Whisper model into memory."""
        logger.info(
            "Loading Faster-Whisper model: %s (device=%s, compute=%s)",
            self.model_size, self.device, self.compute_type,
        )
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        logger.info("Whisper model loaded successfully")

    def transcribe(
        self,
        audio_path: str,
        beam_size: int = 5,
        vad_filter: bool = True,
        word_timestamps: bool = True,
    ) -> List[TranscriptSegment]:
        """
        Transcribe an audio file and return timed segments.

        Args:
            audio_path: Path to WAV/FLAC audio file
            beam_size: Beam search width
            vad_filter: Enable voice activity detection filtering
            word_timestamps: Compute word-level timestamps

        Returns:
            List of TranscriptSegment with start/end times and text
        """
        if self._model is None:
            raise RuntimeError("Transcriber not initialized. Call initialize() first.")

        segments_gen, info = self._model.transcribe(
            audio_path,
            beam_size=beam_size,
            vad_filter=vad_filter,
            word_timestamps=word_timestamps,
            language=self.language,
        )

        detected_language = info.language
        logger.info(
            "Transcribing %s (detected language: %s, probability: %.2f)",
            audio_path, detected_language, info.language_probability,
        )

        segments: List[TranscriptSegment] = []
        for seg in segments_gen:
            segments.append(
                TranscriptSegment(
                    start=round(seg.start, 3),
                    end=round(seg.end, 3),
                    text=seg.text.strip(),
                    confidence=round(seg.avg_log_prob, 4),
                    language=detected_language,
                )
            )

        logger.info("Transcription complete: %d segments", len(segments))
        return segments
