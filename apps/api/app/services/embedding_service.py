"""BYOM embedding generation.

Vaktram never holds a platform LLM key — every embedding is produced with
the user's own provider/key from `UserAIConfig`. If their provider doesn't
support embeddings (Anthropic, Groq, Bedrock today), we silently skip vector
indexing and the search service falls back to FTS-only.

Supported embedding providers:
  openai   → text-embedding-3-small  (1536d) and -3-large (3072d)
  gemini   → text-embedding-004      (768d default)
  cohere   → embed-english-v3.0      (1024d) — requires user to add a Cohere AIConfig
  vertex_ai → text-embedding-004     (via Vertex)
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import UserAIConfig
from app.models.team import MeetingEmbedding
from app.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)
_enc = EncryptionService()


# Providers that natively offer an embeddings endpoint we'll dispatch to.
EMBEDDING_PROVIDERS = {"openai", "gemini", "vertex_ai", "cohere", "azure"}

# Default embedding model per provider (when ai_config doesn't override it).
DEFAULT_MODEL = {
    "openai": "text-embedding-3-small",
    "azure": "text-embedding-3-small",
    "gemini": "text-embedding-004",
    "vertex_ai": "text-embedding-004",
    "cohere": "embed-english-v3.0",
}


class ProviderUnsupported(RuntimeError):
    """Raised when the user's BYOM provider doesn't expose an embeddings API."""


def _decrypt(ai_config: UserAIConfig) -> str | None:
    if not ai_config.api_key_encrypted:
        return None
    try:
        return _enc.decrypt(ai_config.api_key_encrypted)
    except Exception:
        logger.exception("Failed to decrypt user api key")
        return None


def _embedding_model(ai_config: UserAIConfig) -> str:
    extra = ai_config.extra_config or {}
    return (
        extra.get("embedding_model")
        or DEFAULT_MODEL.get(ai_config.provider, "")
    )


async def embed_texts(
    texts: Sequence[str], *, ai_config: UserAIConfig
) -> list[list[float]]:
    """Return one embedding per input text using the user's provider/key.

    Raises ProviderUnsupported if the provider doesn't offer embeddings.
    Raises RuntimeError on missing key.
    """
    if not texts:
        return []
    if ai_config.provider not in EMBEDDING_PROVIDERS:
        raise ProviderUnsupported(
            f"Provider '{ai_config.provider}' does not offer embeddings. "
            "Add an OpenAI, Gemini, Vertex, Cohere, or Azure config to enable "
            "semantic search."
        )

    api_key = _decrypt(ai_config)
    if not api_key and ai_config.provider not in ("vertex_ai",):
        raise RuntimeError(
            f"No API key configured for provider '{ai_config.provider}'."
        )

    if ai_config.provider in ("openai", "azure"):
        return await _openai_embed(texts, api_key, ai_config)
    if ai_config.provider in ("gemini", "vertex_ai"):
        return await _gemini_embed(texts, api_key, ai_config)
    if ai_config.provider == "cohere":
        return await _cohere_embed(texts, api_key, ai_config)
    raise ProviderUnsupported(ai_config.provider)


async def _openai_embed(
    texts: Sequence[str], api_key: str, ai_config: UserAIConfig
) -> list[list[float]]:
    from openai import AsyncOpenAI

    kwargs: dict = {"api_key": api_key}
    if ai_config.provider == "azure" and ai_config.base_url:
        base = ai_config.base_url.rstrip("/")
        if not base.endswith("/openai/v1/"):
            base = base + "/openai/v1/"
        kwargs["base_url"] = base
        api_version = (ai_config.extra_config or {}).get("api_version", "2024-06-01")
        kwargs["default_query"] = {"api-version": api_version}
    client = AsyncOpenAI(**kwargs)
    resp = await client.embeddings.create(
        model=_embedding_model(ai_config), input=list(texts)
    )
    return [d.embedding for d in resp.data]


async def _gemini_embed(
    texts: Sequence[str], api_key: str | None, ai_config: UserAIConfig
) -> list[list[float]]:
    from google import genai

    client_kwargs: dict = {}
    if ai_config.provider == "vertex_ai":
        extra = ai_config.extra_config or {}
        client_kwargs["vertexai"] = True
        client_kwargs["project"] = extra.get("vertex_project", "")
        client_kwargs["location"] = extra.get("vertex_location", "us-central1")
    else:
        client_kwargs["api_key"] = api_key
    client = genai.Client(**client_kwargs)
    model = _embedding_model(ai_config)
    out: list[list[float]] = []
    # google-genai batches up to 100 inputs; chunk just in case.
    for i in range(0, len(texts), 100):
        batch = list(texts[i : i + 100])
        resp = await client.aio.models.embed_content(model=model, contents=batch)
        out.extend(e.values for e in resp.embeddings)
    return out


async def _cohere_embed(
    texts: Sequence[str], api_key: str, ai_config: UserAIConfig
) -> list[list[float]]:
    import httpx

    model = _embedding_model(ai_config)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.cohere.com/v2/embed",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "texts": list(texts),
                "model": model,
                "input_type": "search_document",
                "embedding_types": ["float"],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["embeddings"]["float"]


async def index_segments(
    db: AsyncSession,
    *,
    meeting_id: uuid.UUID,
    segments: list[tuple[uuid.UUID, str]],
    ai_config: UserAIConfig | None,
    batch_size: int = 64,
) -> int:
    """Embed and persist (segment_id, content) tuples. Returns row count.

    Returns 0 when ai_config is missing or the provider doesn't support
    embeddings — the rest of the pipeline (FTS search, summary) keeps working.
    """
    if not segments:
        return 0
    if ai_config is None:
        logger.info("No AI config for meeting %s; skipping embeddings", meeting_id)
        return 0

    try:
        model_name = _embedding_model(ai_config)
        written = 0
        for i in range(0, len(segments), batch_size):
            chunk = segments[i : i + batch_size]
            vectors = await embed_texts(
                [c[1] for c in chunk], ai_config=ai_config
            )
            for (seg_id, content), vec in zip(chunk, vectors, strict=True):
                db.add(
                    MeetingEmbedding(
                        meeting_id=meeting_id,
                        segment_id=seg_id,
                        content=content,
                        embedding={"vector": vec, "dim": len(vec)},
                        embedding_model=f"{ai_config.provider}:{model_name}",
                    )
                )
                written += 1
        return written
    except ProviderUnsupported as exc:
        logger.info("Embeddings skipped for %s: %s", meeting_id, exc)
        return 0
    except Exception:
        logger.exception("Embedding generation failed for %s", meeting_id)
        return 0
