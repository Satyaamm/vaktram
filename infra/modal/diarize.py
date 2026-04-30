"""Modal serverless GPU diarization for Vaktram.

Mirrors the on-prem `apps/workers/diarization/main.py` API exactly so the
Vaktram API doesn't need to know which backend is serving it: POST a
multipart `file` and get back `{"segments": [{start, end, speaker}, ...]}`.

Deploy:
    modal token new
    modal deploy infra/modal/diarize.py

Then set on Fly.io:
    fly secrets set DIARIZATION_SERVICE_URL=https://<workspace>--vaktram-diarize-fastapi-app.modal.run

The function scales to zero — you only pay for compute during actual calls.
At ~$0.01/audio-hour on an L40S the $30 free monthly Modal credit covers
~3,000 hours of diarization before any bill.
"""

from __future__ import annotations

import io
import logging

import modal

logger = logging.getLogger("vaktram.diarize")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "fastapi==0.115.0",
        "pyannote.audio==3.1.1",
        "torch==2.1.2",
        "torchaudio==2.1.2",
        "soundfile==0.12.1",
        "python-multipart==0.0.12",
    )
)

app = modal.App("vaktram-diarize")
hf_secret = modal.Secret.from_name("vaktram-hf-token")  # set: HF_TOKEN=hf_xxx


@app.cls(
    image=image,
    secrets=[hf_secret],
    gpu="L40S",                     # cheapest GPU that runs pyannote 3.1 well
    timeout=900,                    # 15 min max per call
    scaledown_window=120,           # idle 2 min then power down
)
class Diarizer:
    """One Pipeline per container, loaded once at @enter."""

    @modal.enter()
    def load(self):
        import os

        from pyannote.audio import Pipeline
        import torch

        token = os.environ.get("HF_TOKEN")
        if not token:
            raise RuntimeError("HF_TOKEN secret must be set in Modal")

        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token,
        )
        if torch.cuda.is_available():
            self.pipeline.to(torch.device("cuda"))
        logger.info("Diarization pipeline loaded")

    @modal.method()
    def run(self, audio_bytes: bytes) -> dict:
        import soundfile as sf
        import torch

        wav, sr = sf.read(io.BytesIO(audio_bytes))
        if wav.ndim > 1:
            wav = wav.mean(axis=1)  # mono
        waveform = torch.from_numpy(wav).float().unsqueeze(0)

        annotation = self.pipeline({"waveform": waveform, "sample_rate": sr})
        segments = [
            {"start": float(turn.start), "end": float(turn.end), "speaker": speaker}
            for turn, _, speaker in annotation.itertracks(yield_label=True)
        ]
        return {"segments": segments}


@app.function(image=image, timeout=900)
@modal.asgi_app()
def fastapi_app():
    """Wrap the Diarizer class in a FastAPI server with the same surface as
    `apps/workers/diarization/main.py` so the Vaktram API doesn't care which
    backend is serving it."""
    from fastapi import FastAPI, File, UploadFile

    web = FastAPI(title="Vaktram Diarization (Modal)")

    @web.get("/")
    def health():
        return {"status": "ok"}

    @web.post("/diarize")
    async def diarize(file: UploadFile = File(...)):
        audio_bytes = await file.read()
        diarizer = Diarizer()
        result = await diarizer.run.remote.aio(audio_bytes)
        return result

    return web
