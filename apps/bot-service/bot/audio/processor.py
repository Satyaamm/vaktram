"""
Audio processing with FFmpeg.
Converts raw PCM chunks to WAV/FLAC, applies noise reduction,
normalizes volume, and prepares audio for transcription.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16_000
CHANNELS = 1


async def pcm_to_wav(
    input_path: str,
    output_path: Optional[str] = None,
    sample_rate: int = SAMPLE_RATE,
    channels: int = CHANNELS,
) -> str:
    """Convert raw PCM file to WAV format using ffmpeg."""
    if output_path is None:
        output_path = str(Path(input_path).with_suffix(".wav"))

    cmd = [
        "ffmpeg", "-y",
        "-f", "s16le",
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-i", input_path,
        "-acodec", "pcm_s16le",
        output_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg PCM->WAV failed: {stderr.decode()}")

    logger.debug("Converted %s -> %s", input_path, output_path)
    return output_path


async def wav_to_flac(input_path: str, output_path: Optional[str] = None) -> str:
    """Convert WAV to FLAC for efficient storage."""
    if output_path is None:
        output_path = str(Path(input_path).with_suffix(".flac"))

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-acodec", "flac",
        "-compression_level", "5",
        output_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg WAV->FLAC failed: {stderr.decode()}")

    logger.debug("Converted %s -> %s", input_path, output_path)
    return output_path


async def concatenate_chunks(
    chunk_dir: str,
    output_path: str,
    pattern: str = "chunk_*.pcm",
    sample_rate: int = SAMPLE_RATE,
    channels: int = CHANNELS,
) -> str:
    """Concatenate all PCM chunks into a single WAV file."""
    chunk_files = sorted(Path(chunk_dir).glob(pattern))
    if not chunk_files:
        raise FileNotFoundError(f"No chunks matching {pattern} in {chunk_dir}")

    # Create a concat file list for ffmpeg
    list_path = Path(chunk_dir) / "_concat_list.txt"
    with open(list_path, "w") as f:
        for chunk in chunk_files:
            f.write(f"file '{chunk.resolve()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_path),
        "-f", "s16le",
        "-ar", str(sample_rate),
        "-ac", str(channels),
        str(Path(chunk_dir) / "_combined.pcm"),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg concat failed: {stderr.decode()}")

    # Convert the combined PCM to WAV
    combined_pcm = str(Path(chunk_dir) / "_combined.pcm")
    result = await pcm_to_wav(combined_pcm, output_path, sample_rate, channels)

    # Clean up temp files
    os.remove(combined_pcm)
    os.remove(list_path)

    logger.info("Concatenated %d chunks into %s", len(chunk_files), output_path)
    return result


async def normalize_audio(input_path: str, output_path: Optional[str] = None) -> str:
    """Apply loudness normalization using ffmpeg loudnorm filter."""
    if output_path is None:
        base = Path(input_path)
        output_path = str(base.parent / f"{base.stem}_normalized{base.suffix}")

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        output_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg normalize failed: {stderr.decode()}")

    logger.debug("Normalized %s -> %s", input_path, output_path)
    return output_path
