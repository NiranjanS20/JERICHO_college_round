"""
Server-Sent Events (SSE) streaming API route for AgentBreak.

Streams live campaign execution events (attack_started, step, tool_call,
oracle_verdict, iteration_score, attack_finished) over an active HTTP stream.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Attack, Campaign
from app.services.event_bus import event_bus

router = APIRouter(prefix="/api/stream", tags=["stream"])


async def _stream_stored_campaign(campaign: Campaign) -> AsyncGenerator[str, None]:
    """Stream past events of an existing campaign to replay animation in UI."""
    yield f"data: {json.dumps({'event': 'campaign_started', 'campaign_id': campaign.id, 'goals': campaign.goals})}\n\n"
    await asyncio.sleep(0.05)

    for attack in campaign.attacks:
        yield f"data: {json.dumps({'event': 'attack_started', 'attack_id': attack.id, 'campaign_id': campaign.id, 'goal': attack.goal, 'strategy': attack.strategy, 'iteration': attack.iteration})}\n\n"
        await asyncio.sleep(0.05)

        for step in sorted(attack.trace_steps, key=lambda s: s.step_index):
            if step.role == "tool_call":
                yield f"data: {json.dumps({'event': 'tool_call', 'attack_id': attack.id, 'step_index': step.step_index, 'tool_name': step.tool_name, 'tool_args': step.tool_args or {}, 'tool_result': step.tool_result, 'is_malicious': step.is_malicious})}\n\n"
            else:
                yield f"data: {json.dumps({'event': 'step', 'attack_id': attack.id, 'step_index': step.step_index, 'role': step.role, 'content': step.content})}\n\n"
            await asyncio.sleep(0.05)

        if attack.oracle_verdict:
            yield f"data: {json.dumps({'event': 'oracle_verdict', 'attack_id': attack.id, 'verdict': attack.oracle_verdict})}\n\n"
            await asyncio.sleep(0.05)

        yield f"data: {json.dumps({'event': 'attack_finished', 'attack_id': attack.id, 'status': attack.status, 'partial_score': attack.partial_score, 'oracle_verdict': attack.oracle_verdict})}\n\n"
        await asyncio.sleep(0.05)

    yield f"data: {json.dumps({'event': 'campaign_finished', 'campaign_id': campaign.id})}\n\n"


@router.get("/{campaign_id}")
async def stream_campaign_events(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream live or recorded red-team campaign events over Server-Sent Events."""
    # Check campaign existence
    stmt = (
        select(Campaign)
        .options(selectinload(Campaign.attacks).selectinload(Attack.trace_steps))
        .where(Campaign.id == campaign_id)
    )
    res = await db.execute(stmt)
    campaign = res.scalar_one_or_none()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign '{campaign_id}' not found.",
        )

    # If the campaign is still running, attach to live pubsub
    if campaign.status == "running":
        return StreamingResponse(
            event_bus.event_generator(campaign_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Otherwise stream the stored events sequentially
    return StreamingResponse(
        _stream_stored_campaign(campaign),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

