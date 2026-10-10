"""
Campaign API routes for AgentBreak.

Handles creating campaigns, triggering background red-team runs with SSE
broadcasting, and querying campaign execution state.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db, async_session_factory
from app.models import Attack, Campaign, TraceStep
from app.schemas import CampaignCreate, CampaignResponse
from app.services.event_bus import event_bus
from app.victim.agent import VictimAgent
from app.attacker.engine import AdaptiveAttackEngine
from app.defenses import DEFENSE_REGISTRY

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


async def _run_campaign_worker(
    campaign_id: str,
    goals: list[str],
    categories: list[str],
    budget_per_goal: int,
    defense_ids: list[str],
) -> None:
    """Background worker executing adaptive attack runs and streaming SSE events."""
    # Instantiate defenses
    defenses = [DEFENSE_REGISTRY[d_id]() for d_id in defense_ids if d_id in DEFENSE_REGISTRY]
    victim = VictimAgent(defenses=defenses)
    engine = AdaptiveAttackEngine(victim_agent=victim)

    async with async_session_factory() as db:
        for goal in goals:
            # Broadcast campaign attack_started event
            atk_id = f"atk-{uuid.uuid4().hex[:8]}"
            await event_bus.publish(
                campaign_id,
                {
                    "event": "attack_started",
                    "attack_id": atk_id,
                    "campaign_id": campaign_id,
                    "goal": goal,
                    "strategy": "authority_impersonation",
                    "iteration": 1,
                },
            )

            # Run adaptive discovery loop
            result = await engine.run_adaptive_loop(goal=goal, budget=budget_per_goal)

            # Store the best attack record
            best_attempt = result.best_attempt
            verdict_dict = None
            if best_attempt and best_attempt.oracle_verdict:
                v = best_attempt.oracle_verdict
                verdict_dict = {
                    "success": v.success,
                    "violated_policies": v.violated_policies,
                    "violated_policy": v.violated_policy,
                    "severity": v.severity,
                    "evidence": v.evidence,
                    "partial_score": v.partial_score,
                    "details": v.details,
                }

            attack_status = "success" if (verdict_dict and verdict_dict["success"]) else "failure"
            partial_score = best_attempt.partial_score if best_attempt else 0.0

            db_attack = Attack(
                id=atk_id,
                campaign_id=campaign_id,
                goal=goal,
                category=categories[0] if categories else "prompt_injection",
                strategy=best_attempt.strategy_name if best_attempt else "adaptive_search",
                iteration=len(result.attempts),
                injection_point="direct",
                payload=best_attempt.payload if best_attempt else goal,
                status=attack_status,
                oracle_verdict=verdict_dict,
                partial_score=partial_score,
                best_in_chain=True,
            )
            db.add(db_attack)
            await db.flush()

            # Record trace steps
            step_idx = 0
            if best_attempt and best_attempt.victim_result:
                # Add initial user step
                step_user = TraceStep(
                    id=f"step-{uuid.uuid4().hex[:8]}",
                    attack_id=atk_id,
                    step_index=step_idx,
                    role="user",
                    content=best_attempt.payload,
                    is_malicious=True,
                )
                db.add(step_user)
                await event_bus.publish(
                    campaign_id,
                    {
                        "event": "step",
                        "attack_id": atk_id,
                        "step_index": step_idx,
                        "role": "user",
                        "content": best_attempt.payload,
                    },
                )
                step_idx += 1

                # Add tool calls
                for tc in best_attempt.victim_result.tool_calls:
                    step_tc = TraceStep(
                        id=f"step-{uuid.uuid4().hex[:8]}",
                        attack_id=atk_id,
                        step_index=step_idx,
                        role="tool_call",
                        content=f"Called {tc.tool_name}",
                        tool_name=tc.tool_name,
                        tool_args=tc.args,
                        tool_result=tc.result if isinstance(tc.result, dict) else {"raw": str(tc.result)},
                        is_malicious=False,
                    )
                    db.add(step_tc)
                    await event_bus.publish(
                        campaign_id,
                        {
                            "event": "tool_call",
                            "attack_id": atk_id,
                            "step_index": step_idx,
                            "tool_name": tc.tool_name,
                            "tool_args": tc.args,
                            "tool_result": tc.result if isinstance(tc.result, dict) else {"raw": str(tc.result)},
                            "is_malicious": False,
                        },
                    )
                    step_idx += 1

                # Add assistant response
                step_asst = TraceStep(
                    id=f"step-{uuid.uuid4().hex[:8]}",
                    attack_id=atk_id,
                    step_index=step_idx,
                    role="assistant",
                    content=best_attempt.victim_result.final_answer,
                    is_malicious=attack_status == "success",
                )
                db.add(step_asst)
                await event_bus.publish(
                    campaign_id,
                    {
                        "event": "step",
                        "attack_id": atk_id,
                        "step_index": step_idx,
                        "role": "assistant",
                        "content": best_attempt.victim_result.final_answer,
                    },
                )

            # Publish verdict and attack finished events
            if verdict_dict:
                await event_bus.publish(
                    campaign_id,
                    {
                        "event": "oracle_verdict",
                        "attack_id": atk_id,
                        "verdict": verdict_dict,
                    },
                )

            await event_bus.publish(
                campaign_id,
                {
                    "event": "attack_finished",
                    "attack_id": atk_id,
                    "status": attack_status,
                    "partial_score": partial_score,
                    "oracle_verdict": verdict_dict,
                },
            )

        # Update campaign status
        res = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        c = res.scalar_one_or_none()
        if c:
            c.status = "completed"
        await db.commit()

        # Publish final campaign terminal event
        await event_bus.publish(campaign_id, {"event": "campaign_finished", "campaign_id": campaign_id})


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
) -> Campaign:
    """Create a new campaign and start background attack discovery."""
    campaign = Campaign(
        id=f"camp-{uuid.uuid4().hex[:8]}",
        status="running",
        goals=payload.goals,
        categories=payload.categories or ["prompt_injection"],
        budget_per_goal=payload.budget_per_goal,
        defense_ids=payload.defense_ids or [],
        config_snapshot=payload.config_snapshot or {},
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    # Launch background worker
    asyncio.create_task(
        _run_campaign_worker(
            campaign_id=campaign.id,
            goals=payload.goals,
            categories=payload.categories,
            budget_per_goal=payload.budget_per_goal,
            defense_ids=payload.defense_ids,
        )
    )

    return campaign


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
) -> list[Campaign]:
    """Retrieve all campaigns ordered by creation date."""
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
) -> Campaign:
    """Retrieve details for a specific campaign."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign '{campaign_id}' not found.",
        )
    return campaign

