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


@router.get("", response_model=list[AIConfigRead])
async def list_configs(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """List all AI configurations for the authenticated user."""
    result = await db.execute(
        select(UserAIConfig).where(UserAIConfig.user_id == user.id)
    )
    configs = result.scalars().all()
    return [
        AIConfigRead(
            id=c.id,
            user_id=c.user_id,
            provider=c.provider,
            model_name=c.model_name,
            base_url=c.base_url,
            is_default=c.is_default,
            is_active=c.is_active,
            has_api_key=c.api_key_encrypted is not None,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in configs
    ]


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
        is_default=payload.is_default,
        is_active=payload.is_active,
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)

    return AIConfigRead(
        id=config.id,
        user_id=config.user_id,
        provider=config.provider,
        model_name=config.model_name,
        base_url=config.base_url,
        is_default=config.is_default,
        is_active=config.is_active,
        has_api_key=config.api_key_encrypted is not None,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


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

    return AIConfigRead(
        id=config.id,
        user_id=config.user_id,
        provider=config.provider,
        model_name=config.model_name,
        base_url=config.base_url,
        is_default=config.is_default,
        is_active=config.is_active,
        has_api_key=config.api_key_encrypted is not None,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


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


class AIConfigTestResponse(BaseModel):
    success: bool
    message: str
    response_time_ms: float | None = None


@router.post("/test", response_model=AIConfigTestResponse)
async def test_config(
    payload: AIConfigTestRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Test an AI configuration by sending a simple prompt."""
    import time

    try:
        from litellm import acompletion

        start = time.time()
        kwargs: dict = {
            "model": f"{payload.provider}/{payload.model_name}" if payload.provider != "openai" else payload.model_name,
            "messages": [{"role": "user", "content": "Say hello in exactly 3 words."}],
            "max_tokens": 20,
        }
        if payload.api_key:
            kwargs["api_key"] = payload.api_key
        if payload.base_url:
            kwargs["api_base"] = payload.base_url

        response = await acompletion(**kwargs)
        elapsed = round((time.time() - start) * 1000, 1)
        return AIConfigTestResponse(
            success=True,
            message="Connection successful!",
            response_time_ms=elapsed,
        )
    except ImportError:
        return AIConfigTestResponse(
            success=False,
            message="LiteLLM not installed on this server.",
        )
    except Exception as exc:
        return AIConfigTestResponse(
            success=False,
            message=f"Connection failed: {str(exc)[:200]}",
        )
