"""
Metrics API routes for AgentBreak.

Computes campaign-level and global aggregate red-team metrics,
attack success rates (ASR), and OWASP / strategy distributions.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Attack, Campaign
from app.schemas import MetricsSummaryResponse

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    campaign_id: Optional[str] = Query(None, description="Campaign ID to calculate metrics for"),
    db: AsyncSession = Depends(get_db),
) -> MetricsSummaryResponse:
    """Aggregate red-team metrics, success rates, and vulnerability breakdowns."""
    target_campaign_id = campaign_id

    # If no campaign specified, select the latest campaign
    if not target_campaign_id:
        camp_stmt = select(Campaign).order_by(Campaign.created_at.desc()).limit(1)
        res = await db.execute(camp_stmt)
        latest_camp = res.scalar_one_or_none()
        if latest_camp:
            target_campaign_id = latest_camp.id
        else:
            return MetricsSummaryResponse(campaign_id="none")

    stmt = select(Attack).where(Attack.campaign_id == target_campaign_id)
    res = await db.execute(stmt)
    attacks = list(res.scalars().all())

    total = len(attacks)
    successful = sum(1 for a in attacks if a.status == "success")
    failed = sum(1 for a in attacks if a.status == "failure")
    error = sum(1 for a in attacks if a.status == "error")

    overall_asr = round(successful / total, 4) if total > 0 else 0.0
    avg_score = round(sum(a.partial_score for a in attacks) / total, 4) if total > 0 else 0.0

    category_breakdown: dict[str, dict[str, Any]] = {}
    strategy_breakdown: dict[str, dict[str, Any]] = {}

    for a in attacks:
        # Category breakdown
        cat = a.category
        if cat not in category_breakdown:
            category_breakdown[cat] = {"total": 0, "successful": 0, "asr": 0.0}
        category_breakdown[cat]["total"] += 1
        if a.status == "success":
            category_breakdown[cat]["successful"] += 1

        # Strategy breakdown
        strat = a.strategy
        if strat not in strategy_breakdown:
            strategy_breakdown[strat] = {"total": 0, "successful": 0, "asr": 0.0}
        strategy_breakdown[strat]["total"] += 1
        if a.status == "success":
            strategy_breakdown[strat]["successful"] += 1

    # Calculate sub-ASRs
    for cat_data in category_breakdown.values():
        cat_data["asr"] = round(cat_data["successful"] / cat_data["total"], 4) if cat_data["total"] > 0 else 0.0

    for strat_data in strategy_breakdown.values():
        strat_data["asr"] = round(strat_data["successful"] / strat_data["total"], 4) if strat_data["total"] > 0 else 0.0

    return MetricsSummaryResponse(
        campaign_id=target_campaign_id,
        total_attacks=total,
        successful_attacks=successful,
        failed_attacks=failed,
        error_attacks=error,
        overall_asr=overall_asr,
        avg_partial_score=avg_score,
        category_breakdown=category_breakdown,
        strategy_breakdown=strategy_breakdown,
    )

