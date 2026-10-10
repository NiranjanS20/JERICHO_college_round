"""
Attack API routes for AgentBreak.

Provides listing attacks, detailed inspection with full traces and oracle verdicts,
and statistical replay evaluations with Wilson confidence intervals.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Attack, ReplayResult as DBReplayResult
from app.schemas import (
    AttackResponse,
    AttackSummaryResponse,
    ReplayRequest,
    ReplayResponse,
)
from app.traces.replay import ReplayEngine
from app.defenses import DEFENSE_REGISTRY

router = APIRouter(prefix="/api/attacks", tags=["attacks"])


@router.get("", response_model=list[AttackSummaryResponse])
async def list_attacks(
    campaign_id: Optional[str] = Query(None, description="Filter attacks by campaign ID"),
    db: AsyncSession = Depends(get_db),
) -> list[Attack]:
    """Retrieve attacks, optionally filtered by campaign ID."""
    stmt = select(Attack).order_by(Attack.created_at.desc())
    if campaign_id:
        stmt = stmt.where(Attack.campaign_id == campaign_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{attack_id}", response_model=AttackResponse)
async def get_attack(
    attack_id: str,
    db: AsyncSession = Depends(get_db),
) -> Attack:
    """Retrieve full attack details including trace steps and oracle verdict."""
    stmt = (
        select(Attack)
        .options(selectinload(Attack.trace_steps))
        .where(Attack.id == attack_id)
    )
    result = await db.execute(stmt)
    attack = result.scalar_one_or_none()
    if not attack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attack '{attack_id}' not found.",
        )
    return attack


@router.post("/{attack_id}/replay", response_model=ReplayResponse)
async def replay_attack(
    attack_id: str,
    request: ReplayRequest,
    db: AsyncSession = Depends(get_db),
) -> DBReplayResult:
    """Re-run a stored attack N times to measure reproducibility and defense resilience."""
    # Fetch attack record to verify existence and retrieve payload
    stmt = select(Attack).where(Attack.id == attack_id)
    result = await db.execute(stmt)
    attack = result.scalar_one_or_none()
    if not attack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attack '{attack_id}' not found.",
        )

    # Instantiate chosen defenses
    defenses = [
        DEFENSE_REGISTRY[d_id]()
        for d_id in request.defense_ids
        if d_id in DEFENSE_REGISTRY
    ]

    engine = ReplayEngine()
    replay_out = await engine.replay(
        attack_id=attack_id,
        payload=attack.payload,
        n_runs=request.n_runs,
        defenses=defenses,
        session=db,
    )

    db_replay = DBReplayResult(
        id=f"rep-{uuid.uuid4().hex[:8]}",
        attack_id=attack_id,
        n_runs=replay_out.n_runs,
        successes=replay_out.successes,
        success_rate=replay_out.success_rate,
        wilson_ci_low=replay_out.wilson_ci_low,
        wilson_ci_high=replay_out.wilson_ci_high,
        defenses_used=replay_out.defenses_used,
    )
    db.add(db_replay)
    await db.commit()
    await db.refresh(db_replay)

    return db_replay



# In-memory storage for counterfactual reports
_COUNTERFACTUAL_REPORTS: dict[str, dict] = {}


@router.post("/{attack_id}/counterfactual")
async def run_counterfactual_analysis(
    attack_id: str,
    n_runs: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Run counterfactual ablation analysis to localize the takeover point."""
    stmt = (
        select(Attack)
        .options(selectinload(Attack.trace_steps))
        .where(Attack.id == attack_id)
    )
    result = await db.execute(stmt)
    attack = result.scalar_one_or_none()
    if not attack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attack '{attack_id}' not found.",
        )

    trace_steps_data = [
        {
            "step_index": s.step_index,
            "role": s.role,
            "content": s.content,
            "tool_name": s.tool_name,
            "tool_args": s.tool_args,
            "tool_result": s.tool_result,
        }
        for s in attack.trace_steps
    ]

    from app.traces.counterfactual import CounterfactualEngine
    cf_engine = CounterfactualEngine()
    report = await cf_engine.analyze(
        attack_id=attack_id,
        raw_payload=attack.payload,
        trace_steps=trace_steps_data,
        n_runs=n_runs,
    )

    report_dict = {
        "attack_id": report.attack_id,
        "baseline_n_runs": report.baseline_n_runs,
        "baseline_successes": report.baseline_successes,
        "baseline_success_rate": report.baseline_success_rate,
        "baseline_ci_low": report.baseline_ci_low,
        "baseline_ci_high": report.baseline_ci_high,
        "elements": report.elements,
        "ablations": report.ablations,
        "takeover_elements": report.takeover_elements,
        "takeover_step_index": report.takeover_step_index,
        "minimal_cause_set": report.minimal_cause_set,
        "confidence_label": report.confidence_label,
        "disclaimer": report.disclaimer,
    }
    _COUNTERFACTUAL_REPORTS[attack_id] = report_dict
    return report_dict


@router.get("/{attack_id}/counterfactual")
async def get_counterfactual_analysis(attack_id: str):
    """Retrieve existing counterfactual report for an attack."""
    report = _COUNTERFACTUAL_REPORTS.get(attack_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No counterfactual analysis found for attack '{attack_id}'. Run POST first.",
        )
    return report

