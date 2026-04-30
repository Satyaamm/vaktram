"""
Diarization Service — lightweight FastAPI server wrapping pyannote.audio.
Receives audio files via HTTP, returns speaker segments.
Runs as a Docker container.
"""

import logging
import os
import tempfile

import torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from pyannote.audio import Pipeline

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("diarization-service")

HF_TOKEN = os.getenv("HF_TOKEN", "")
MODEL_NAME = os.getenv("DIARIZATION_MODEL", "pyannote/speaker-diarization-3.1")

app = FastAPI(title="Vaktram Diarization Service", version="0.1.0")

# Global pipeline (loaded once at startup)
_pipeline: Pipeline | None = None


@app.on_event("startup")
async def load_model():
    global _pipeline
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Loading diarization model %s on %s...", MODEL_NAME, device)

    if not HF_TOKEN:
        logger.warning("HF_TOKEN not set — pyannote models require a HuggingFace token")

    _pipeline = Pipeline.from_pretrained(MODEL_NAME, use_auth_token=HF_TOKEN or None)
    _pipeline.to(device)
    logger.info("Diarization model loaded successfully")


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": _pipeline is not None}


@app.post("/diarize")
async def diarize(file: UploadFile = File(...)):
    """Accept an audio file and return speaker diarization segments.

    Returns:
        {"segments": [{"start": 0.0, "end": 4.2, "speaker": "SPEAKER_00"}, ...],
         "speaker_count": 3}
    """
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    # Save uploaded file to temp
    suffix = os.path.splitext(file.filename or "audio.wav")[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        logger.info("Running diarization on %s (%d bytes)", file.filename, len(content))
        diarization = _pipeline(tmp_path)

        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": round(turn.start, 3),
                "end": round(turn.end, 3),
                "speaker": speaker,
            })

        speakers = set(s["speaker"] for s in segments)
        logger.info("Diarization complete: %d turns, %d speakers", len(segments), len(speakers))

        return {"segments": segments, "speaker_count": len(speakers)}

    except Exception as exc:
        logger.exception("Diarization failed")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=False)
