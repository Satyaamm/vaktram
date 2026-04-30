"""Ask — chat with your meetings, powered by Vakta (Vaktram's RAG assistant)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.intel import AskMessage, AskScope, AskThread
from app.models.team import UserProfile
from app.services import ask_service
from app.services.ask_service import NoAIConfigError

router = APIRouter(prefix="/ask", tags=["ask"])


class CreateThreadRequest(BaseModel):
    title: str | None = None
    scope: AskScope = AskScope.organization
    scope_id: uuid.UUID | None = None


class AskRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


@router.post("/threads")
async def create_thread(
    body: CreateThreadRequest,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thread = AskThread(
        user_id=user.id,
        organization_id=user.organization_id,
        title=body.title,
        scope=body.scope,
        scope_id=body.scope_id,
    )
    db.add(thread)
    await db.flush()
    return {"id": str(thread.id), "title": thread.title, "scope": thread.scope.value}


@router.get("/threads")
async def list_threads(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 30,
):
    rows = (await db.execute(
        select(AskThread)
        .where(AskThread.user_id == user.id)
        .order_by(AskThread.created_at.desc())
        .limit(limit)
    )).scalars().all()
    return [
        {"id": str(t.id), "title": t.title, "scope": t.scope.value, "created_at": t.created_at}
        for t in rows
    ]


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: uuid.UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thread = await db.get(AskThread, thread_id)
    if not thread or thread.user_id != user.id:
        raise HTTPException(404, "Thread not found")
    msgs = (await db.execute(
        select(AskMessage)
        .where(AskMessage.thread_id == thread.id)
        .order_by(AskMessage.created_at.asc())
    )).scalars().all()
    return {
        "id": str(thread.id),
        "title": thread.title,
        "scope": thread.scope.value,
        "scope_id": str(thread.scope_id) if thread.scope_id else None,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "citations": m.citations or [],
                "created_at": m.created_at,
            }
            for m in msgs
        ],
    }


@router.post("/threads/{thread_id}/messages")
async def send_message(
    thread_id: uuid.UUID,
    body: AskRequest,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thread = await db.get(AskThread, thread_id)
    if not thread or thread.user_id != user.id:
        raise HTTPException(404, "Thread not found")
    try:
        assistant = await ask_service.answer(
            db,
            user_id=user.id,
            organization_id=user.organization_id,
            thread=thread,
            question=body.message,
        )
    except NoAIConfigError as e:
        # 412 Precondition Failed — UI uses this to show "Configure AI" CTA.
        raise HTTPException(
            status_code=412,
            detail={"error": "no_ai_config", "message": str(e)},
        )
    return {
        "id": str(assistant.id),
        "role": assistant.role,
        "content": assistant.content,
        "citations": assistant.citations or [],
    }
