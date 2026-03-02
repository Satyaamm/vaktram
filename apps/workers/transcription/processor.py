"""
Combines Faster-Whisper transcription with pyannote diarization.
Aligns speaker labels with transcript segments for speaker-attributed text.
"""

import logging
from typing import Any, Dict, List, Optional

from transcriber import Transcriber, TranscriptSegment
from diarizer import Diarizer, DiarizationSegment

logger = logging.getLogger(__name__)


class TranscriptionProcessor:
    """
    Orchestrates transcription and diarization, then merges
    the results into speaker-attributed transcript segments.
    """

    def __init__(
        self,
        whisper_model_size: str = "large-v3",
        device: str = "auto",
    ):
        self._transcriber = Transcriber(
            model_size=whisper_model_size,
            device=device,
        )
        self._diarizer = Diarizer(device=device)

    async def initialize(self) -> None:
        """Load both models."""
        self._transcriber.initialize()
        self._diarizer.initialize()
        logger.info("TranscriptionProcessor initialized")

    async def process(self, audio_path: str) -> Dict[str, Any]:
        """
        Run full transcription + diarization pipeline.

        Returns dict with:
            - segments: list of {speaker, start, end, text, confidence}
            - language: detected language
            - speaker_count: number of unique speakers
        """
        # Step 1: Transcribe
        transcript_segments = self._transcriber.transcribe(audio_path)

        # Step 2: Diarize
        diarization_segments = self._diarizer.diarize(audio_path)

        # Step 3: Merge - assign speaker labels to transcript segments
        merged = self._merge_segments(transcript_segments, diarization_segments)

        speakers = set(s["speaker"] for s in merged)
        language = transcript_segments[0].language if transcript_segments else "unknown"

        return {
            "segments": merged,
            "language": language,
            "speaker_count": len(speakers),
        }

    @staticmethod
    def _merge_segments(
        transcript_segments: List[TranscriptSegment],
        diarization_segments: List[DiarizationSegment],
    ) -> List[Dict[str, Any]]:
        """
        Assign a speaker label to each transcript segment based on
        maximum temporal overlap with diarization segments.
        """
        merged = []

        for tseg in transcript_segments:
            best_speaker = "UNKNOWN"
            best_overlap = 0.0

            for dseg in diarization_segments:
                # Calculate overlap between transcript and diarization segments
                overlap_start = max(tseg.start, dseg.start)
                overlap_end = min(tseg.end, dseg.end)
                overlap_duration = max(0.0, overlap_end - overlap_start)

                if overlap_duration > best_overlap:
                    best_overlap = overlap_duration
                    best_speaker = dseg.speaker

            merged.append({
                "speaker": best_speaker,
                "start": tseg.start,
                "end": tseg.end,
                "text": tseg.text,
                "confidence": tseg.confidence,
            })

        return merged
