"""BYOM AI config CRUD endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.ai_config import UserAIConfig
from app.models.team import UserProfile
from app.schemas.ai_config import AIConfigCreate, AIConfigRead, AIConfigUpdate
from app.services.encryption_service import EncryptionService

router = APIRouter(prefix="/ai-config", tags=["ai-config"])
encryption = EncryptionService()


def _config_to_read(c: UserAIConfig) -> AIConfigRead:
    return AIConfigRead(
        id=c.id,
        user_id=c.user_id,
        provider=c.provider,
        model_name=c.model_name,
        base_url=c.base_url,
        extra_config=c.extra_config,
        is_default=c.is_default,
        is_active=c.is_active,
        has_api_key=c.api_key_encrypted is not None,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=list[AIConfigRead])
async def list_configs(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """List all AI configurations for the authenticated user."""
    result = await db.execute(
        select(UserAIConfig).where(UserAIConfig.user_id == user.id)
    )
    return [_config_to_read(c) for c in result.scalars().all()]


@router.get("/status")
async def config_status(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Quick boolean for the UI: has the user configured an LLM provider?

    Frontend uses this to gate features that require BYOM (summaries, Vakta,
    semantic search) and surface the "Configure AI" CTA.
    """
    row = (await db.execute(
        select(UserAIConfig)
        .where(UserAIConfig.user_id == user.id, UserAIConfig.is_active.is_(True))
        .order_by(UserAIConfig.is_default.desc(), UserAIConfig.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    if row is None:
        return {"configured": False, "provider": None, "model": None}
    return {
        "configured": True,
        "provider": row.provider,
        "model": row.model_name,
        "is_default": row.is_default,
    }


@router.post("", response_model=AIConfigRead, status_code=status.HTTP_201_CREATED)
async def create_config(
    payload: AIConfigCreate,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Create a new AI configuration."""
    encrypted_key = encryption.encrypt(payload.api_key) if payload.api_key else None

    # If setting as default, unset any existing default
    if payload.is_default:
        await db.execute(
            update(UserAIConfig)
            .where(UserAIConfig.user_id == user.id, UserAIConfig.is_default.is_(True))
            .values(is_default=False)
        )

    config = UserAIConfig(
        user_id=user.id,
        provider=payload.provider,
        model_name=payload.model_name,
        api_key_encrypted=encrypted_key,
        base_url=payload.base_url,
        extra_config=payload.extra_config or {},
        is_default=payload.is_default,
        is_active=payload.is_active,
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)

    return _config_to_read(config)


@router.patch("/{config_id}", response_model=AIConfigRead)
async def update_config(
    config_id: uuid.UUID,
    payload: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Update an AI configuration."""
    result = await db.execute(
        select(UserAIConfig).where(
            UserAIConfig.id == config_id, UserAIConfig.user_id == user.id
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise HTTPException(status_code=404, detail="AI config not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "api_key" in update_data:
        api_key = update_data.pop("api_key")
        config.api_key_encrypted = encryption.encrypt(api_key) if api_key else None

    if update_data.get("is_default"):
        await db.execute(
            update(UserAIConfig)
            .where(UserAIConfig.user_id == user.id, UserAIConfig.is_default.is_(True))
            .values(is_default=False)
        )

    for field, value in update_data.items():
        setattr(config, field, value)

    await db.flush()
    await db.refresh(config)

    return _config_to_read(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Delete an AI configuration."""
    result = await db.execute(
        delete(UserAIConfig).where(
            UserAIConfig.id == config_id, UserAIConfig.user_id == user.id
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="AI config not found")


class AIConfigTestRequest(BaseModel):
    provider: str
    model_name: str
    api_key: str | None = None
    base_url: str | None = None
    extra_config: dict | None = None


class AIConfigTestResponse(BaseModel):
    success: bool
    message: str
    response_time_ms: float | None = None


@router.post("/test", response_model=AIConfigTestResponse)
async def test_config(
    payload: AIConfigTestRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Test an AI configuration by sending a simple prompt via native provider SDK."""
    import time

    from app.services.llm_service import LLMRequest, call_llm

    try:
        start = time.time()

        req = LLMRequest(
            provider=payload.provider,
            model_name=payload.model_name,
            api_key=payload.api_key,
            base_url=payload.base_url,
            extra_config=payload.extra_config,
            user_prompt="Say hello in exactly 3 words.",
            max_tokens=20,
        )

        await call_llm(req)
        elapsed = round((time.time() - start) * 1000, 1)
        return AIConfigTestResponse(
            success=True,
            message="Connection successful!",
            response_time_ms=elapsed,
        )
    except Exception as exc:
        error_msg = _friendly_error(exc)
        return AIConfigTestResponse(
            success=False,
            message=f"Connection failed: {error_msg}",
        )


def _friendly_error(exc: Exception) -> str:
    """Convert native SDK exceptions into user-friendly messages."""
    exc_type = type(exc).__name__
    raw = str(exc)

    # OpenAI / Anthropic / Groq — AuthenticationError class
    if exc_type == "AuthenticationError" or "invalid" in raw.lower() and "key" in raw.lower():
        return "Authentication failed. Please check your API key."

    # Google Gemini — ClientError with API_KEY_INVALID
    if "API key not valid" in raw or "API_KEY_INVALID" in raw:
        return "Authentication failed. Please check your API key."

    # Model not found
    if exc_type == "NotFoundError" or "not found" in raw.lower() and "model" in raw.lower():
        return "Model not found. Please check the model name."

    # Rate limiting
    if exc_type == "RateLimitError" or "rate limit" in raw.lower() or "quota" in raw.lower():
        return "Rate limited. The API key works but you've hit rate limits."

    # Permission denied (Bedrock, Vertex)
    if "AccessDeniedException" in raw or "permission" in raw.lower():
        return "Access denied. Please check your credentials and permissions."

    # Connection / network errors
    if "Could not resolve host" in raw or "ConnectError" in exc_type or "ConnectionError" in exc_type:
        return "Connection failed. Please check the endpoint URL."

    # Bedrock-specific
    if "UnrecognizedClientException" in raw:
        return "Authentication failed. Please check your AWS credentials."

    # Google Vertex — credentials
    if "Could not automatically determine credentials" in raw:
        return "GCP credentials not found. Please provide a service account JSON."

    return raw[:200]
