"""
Demo API routes for AgentBreak.

Provides instant offline loading of pre-run campaigns from cached JSON files,
allowing the entire platform and frontend to be demonstrated without live LLM calls.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Attack, Campaign, EvalMatrixResult, ReplayResult, TraceStep

router = APIRouter(prefix="/api/demo", tags=["demo"])

DEMO_CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "demo_cache" / "campaign_001.json"


class DemoLoadResponse(BaseModel):
    """Status of loading cached demo data."""
    status: str
    campaign_id: str
    attacks_loaded: int
    eval_matrix_rows_loaded: int
    message: str


@router.post("/load", response_model=DemoLoadResponse)
async def load_demo_campaign(
    db: AsyncSession = Depends(get_db),
) -> DemoLoadResponse:
    """Load cached pre-computed campaign findings into the local database."""
    if not DEMO_CACHE_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo cache file not found at {DEMO_CACHE_PATH}",
        )

    try:
        with open(DEMO_CACHE_PATH, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read demo cache: {exc}",
        )

    campaign_id = data.get("id", "demo-campaign-001")

    # Check if this campaign already exists; if so, delete existing records to ensure fresh state
    existing = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    camp_obj = existing.scalar_one_or_none()
    if camp_obj:
        await db.delete(camp_obj)
        await db.commit()

    created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow()

    # Create Campaign
    campaign = Campaign(
        id=campaign_id,
        status=data.get("status", "completed"),
        goals=data.get("goals", []),
        categories=data.get("categories", []),
        budget_per_goal=data.get("budget_per_goal", 5),
        defense_ids=data.get("defense_ids", []),
        config_snapshot=data.get("config_snapshot", {}),
        created_at=created_at,
    )
    db.add(campaign)
    await db.flush()

    # Load Attacks and Trace Steps
    attacks_count = 0
    for atk_data in data.get("attacks", []):
        atk_id = atk_data["id"]
        attack = Attack(
            id=atk_id,
            campaign_id=campaign_id,
            goal=atk_data["goal"],
            category=atk_data["category"],
            strategy=atk_data["strategy"],
            iteration=atk_data.get("iteration", 1),
            injection_point=atk_data.get("injection_point", "direct"),
            payload=atk_data["payload"],
            status=atk_data.get("status", "success"),
            oracle_verdict=atk_data.get("oracle_verdict"),
            partial_score=atk_data.get("partial_score", 0.0),
            best_in_chain=atk_data.get("best_in_chain", True),
            created_at=datetime.fromisoformat(atk_data["created_at"]) if atk_data.get("created_at") else created_at,
        )
        db.add(attack)
        await db.flush()
        attacks_count += 1

        # Trace steps
        for step_data in atk_data.get("trace_steps", []):
            step = TraceStep(
                id=f"step-{atk_id}-{step_data['step_index']}",
                attack_id=atk_id,
                step_index=step_data["step_index"],
                role=step_data["role"],
                content=step_data["content"],
                tool_name=step_data.get("tool_name"),
                tool_args=step_data.get("tool_args"),
                tool_result=step_data.get("tool_result"),
                is_malicious=step_data.get("is_malicious", False),
                timestamp=datetime.fromisoformat(step_data["timestamp"]) if step_data.get("timestamp") else created_at,
            )
            db.add(step)

        # Replay results if present
        for rep_idx, rep_data in enumerate(atk_data.get("replays", [])):
            replay = ReplayResult(
                id=f"rep-{atk_id}-{rep_idx}",
                attack_id=atk_id,
                n_runs=rep_data["n_runs"],
                successes=rep_data["successes"],
                success_rate=rep_data["success_rate"],
                wilson_ci_low=rep_data["wilson_ci_low"],
                wilson_ci_high=rep_data["wilson_ci_high"],
                defenses_used=rep_data.get("defenses_used", []),
                created_at=created_at,
            )
            db.add(replay)

    # Load Eval Matrix rows
    matrix_count = 0
    for m_idx, m_data in enumerate(data.get("eval_matrix", [])):
        em_row = EvalMatrixResult(
            id=f"emr-{campaign_id}-{m_idx}",
            campaign_id=campaign_id,
            defense_combo=m_data.get("defense_combo", []),
            attack_success_rate=m_data.get("attack_success_rate", 0.0),
            benign_pass_rate=m_data.get("benign_pass_rate", 1.0),
            regressions=m_data.get("regressions"),
            adaptive_asr=m_data.get("adaptive_asr", 0.0),
            static_asr=m_data.get("static_asr", 0.0),
            created_at=created_at,
        )
        db.add(em_row)
        matrix_count += 1

    await db.commit()

    return DemoLoadResponse(
        status="success",
        campaign_id=campaign_id,
        attacks_loaded=attacks_count,
        eval_matrix_rows_loaded=matrix_count,
        message="Demo campaign pre-run findings loaded successfully into database.",
    )

