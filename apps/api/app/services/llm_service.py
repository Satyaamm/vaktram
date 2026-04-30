"""Native LLM provider integrations (no wrapper libraries).

Each provider uses its official SDK:
- OpenAI / Azure OpenAI / Ollama / Custom: openai SDK
- Anthropic: anthropic SDK
- Google Gemini: google-genai SDK
- Google Vertex AI: google-genai SDK (vertexai=True)
- Groq: groq SDK
- AWS Bedrock: boto3 SDK
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """Unified request params for any provider."""
    provider: str
    model_name: str
    api_key: str | None = None
    base_url: str | None = None
    extra_config: dict | None = None
    system_prompt: str | None = None
    user_prompt: str = ""
    temperature: float = 0.3
    max_tokens: int = 2048


async def call_llm(req: LLMRequest) -> str:
    """Route to the correct provider SDK and return the text response."""
    provider = req.provider

    if provider in ("openai", "azure", "ollama", "custom", "azure_ai"):
        return await _call_openai_compatible(req)
    elif provider == "anthropic":
        return await _call_anthropic(req)
    elif provider == "gemini":
        return await _call_gemini(req)
    elif provider == "vertex_ai":
        return await _call_vertex_ai(req)
    elif provider == "groq":
        return await _call_groq(req)
    elif provider == "bedrock":
        return await _call_bedrock(req)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


# ---------------------------------------------------------------------------
# OpenAI / Azure OpenAI / Ollama / Custom (all use the openai SDK)
# ---------------------------------------------------------------------------

async def _call_openai_compatible(req: LLMRequest) -> str:
    """OpenAI SDK handles: OpenAI, Azure OpenAI, Azure AI Studio, Ollama, Custom endpoints."""
    from openai import AsyncOpenAI

    extra = req.extra_config or {}

    # Build client kwargs
    client_kwargs: dict = {}

    if req.provider == "azure":
        # Azure OpenAI: base_url = https://resource.openai.azure.com/openai/v1/
        base = req.base_url or ""
        if base and not base.endswith("/openai/v1/"):
            base = base.rstrip("/") + "/openai/v1/"
        client_kwargs["base_url"] = base
        client_kwargs["api_key"] = req.api_key
        # Azure api_version is passed via default_query
        api_version = extra.get("api_version", "2024-06-01")
        client_kwargs["default_query"] = {"api-version": api_version}

    elif req.provider == "azure_ai":
        # Azure AI Studio: direct endpoint
        client_kwargs["base_url"] = req.base_url
        client_kwargs["api_key"] = req.api_key

    elif req.provider == "ollama":
        # Ollama exposes OpenAI-compatible API
        client_kwargs["base_url"] = (req.base_url or "http://localhost:11434") + "/v1"
        client_kwargs["api_key"] = "ollama"  # dummy key required by SDK

    elif req.provider == "custom":
        # Custom OpenAI-compatible endpoint
        client_kwargs["base_url"] = req.base_url
        client_kwargs["api_key"] = req.api_key or "no-key"

    else:
        # Standard OpenAI
        client_kwargs["api_key"] = req.api_key

    client = AsyncOpenAI(**client_kwargs)

    messages: list[dict] = []
    if req.system_prompt:
        messages.append({"role": "system", "content": req.system_prompt})
    messages.append({"role": "user", "content": req.user_prompt})

    response = await client.chat.completions.create(
        model=req.model_name,
        messages=messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Anthropic (anthropic SDK)
# ---------------------------------------------------------------------------

async def _call_anthropic(req: LLMRequest) -> str:
    """Anthropic Claude via the official anthropic SDK."""
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=req.api_key)

    kwargs: dict = {
        "model": req.model_name,
        "max_tokens": req.max_tokens,
        "messages": [{"role": "user", "content": req.user_prompt}],
    }
    if req.system_prompt:
        kwargs["system"] = req.system_prompt
    if req.temperature is not None:
        kwargs["temperature"] = req.temperature

    response = await client.messages.create(**kwargs)
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Google Gemini (google-genai SDK)
# ---------------------------------------------------------------------------

async def _call_gemini(req: LLMRequest) -> str:
    """Google Gemini via the official google-genai SDK."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=req.api_key)

    config = types.GenerateContentConfig(
        max_output_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    if req.system_prompt:
        config.system_instruction = req.system_prompt

    response = await client.aio.models.generate_content(
        model=req.model_name,
        contents=req.user_prompt,
        config=config,
    )
    return response.text.strip()


# ---------------------------------------------------------------------------
# Google Vertex AI (google-genai SDK with vertexai=True)
# ---------------------------------------------------------------------------

async def _call_vertex_ai(req: LLMRequest) -> str:
    """GCP Vertex AI via google-genai SDK."""
    from google import genai
    from google.genai import types

    extra = req.extra_config or {}
    project = extra.get("vertex_project", "")
    location = extra.get("vertex_location", "us-central1")

    client_kwargs: dict = {
        "vertexai": True,
        "project": project,
        "location": location,
    }

    # If service account JSON is provided, write to temp file for auth
    vertex_credentials = extra.get("vertex_credentials")
    if vertex_credentials:
        import tempfile
        import os
        creds_data = vertex_credentials
        # If it's a JSON string, parse to validate
        if isinstance(creds_data, str):
            try:
                json.loads(creds_data)
            except json.JSONDecodeError:
                raise ValueError("Invalid service account JSON for Vertex AI")
            # Write to temp file and set env var for google auth
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            tmp.write(creds_data)
            tmp.close()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

    client = genai.Client(**client_kwargs)

    config = types.GenerateContentConfig(
        max_output_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    if req.system_prompt:
        config.system_instruction = req.system_prompt

    response = await client.aio.models.generate_content(
        model=req.model_name,
        contents=req.user_prompt,
        config=config,
    )
    return response.text.strip()


# ---------------------------------------------------------------------------
# Groq (groq SDK — OpenAI-compatible interface)
# ---------------------------------------------------------------------------

async def _call_groq(req: LLMRequest) -> str:
    """Groq via the official groq SDK."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=req.api_key)

    messages: list[dict] = []
    if req.system_prompt:
        messages.append({"role": "system", "content": req.system_prompt})
    messages.append({"role": "user", "content": req.user_prompt})

    response = await client.chat.completions.create(
        model=req.model_name,
        messages=messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# AWS Bedrock (boto3 SDK — Converse API)
# ---------------------------------------------------------------------------

async def _call_bedrock(req: LLMRequest) -> str:
    """AWS Bedrock via boto3 Converse API (run in thread to avoid blocking)."""
    import asyncio
    import functools

    def _sync_call() -> str:
        import boto3

        extra = req.extra_config or {}
        client_kwargs: dict = {
            "service_name": "bedrock-runtime",
            "region_name": extra.get("aws_region_name", "us-east-1"),
        }
        if extra.get("aws_access_key_id") and extra.get("aws_secret_access_key"):
            client_kwargs["aws_access_key_id"] = extra["aws_access_key_id"]
            client_kwargs["aws_secret_access_key"] = extra["aws_secret_access_key"]

        client = boto3.client(**client_kwargs)

        messages = [
            {
                "role": "user",
                "content": [{"text": req.user_prompt}],
            }
        ]

        converse_kwargs: dict = {
            "modelId": req.model_name,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": req.max_tokens,
                "temperature": req.temperature,
            },
        }
        if req.system_prompt:
            converse_kwargs["system"] = [{"text": req.system_prompt}]

        response = client.converse(**converse_kwargs)
        return response["output"]["message"]["content"][0]["text"].strip()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_call)
