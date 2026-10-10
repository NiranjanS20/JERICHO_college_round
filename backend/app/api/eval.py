"""
Evaluation Matrix API routes for AgentBreak.

Orchestrates Attacks × Defenses matrix evaluations, comparing attack success rates,
benign utility retention, regressions, and adaptive vs static discovery.
"""

from __future__ import annotations

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import EvalMatrixResult as DBEvalMatrixResult, Campaign
from app.schemas import EvalMatrixRequest, EvalMatrixResponse
from app.eval.matrix import EvalMatrixRunner, CURATED_DEFENSE_COMBINATIONS

router = APIRouter(prefix="/api/eval", tags=["evaluation"])


@router.post("/matrix", response_model=list[EvalMatrixResponse])
async def execute_eval_matrix(
    payload: EvalMatrixRequest,
    db: AsyncSession = Depends(get_db),
) -> list[DBEvalMatrixResult]:
    """Execute the Attacks × Defenses evaluation matrix for a campaign."""
    # Build combinations list
    combos = []
    if payload.defense_combos:
        for idx, combo in enumerate(payload.defense_combos):
            combos.append({
                "id": f"combo_{idx}",
                "name": " + ".join(combo) if combo else "No Defenses",
                "defenses": combo,
            })
    else:
        combos = CURATED_DEFENSE_COMBINATIONS

    runner = EvalMatrixRunner()
    run_result = await runner.run_matrix(
        campaign_id=payload.campaign_id,
        combos=combos,
        include_benign=payload.include_benign,
        budget_k=2,
    )

    db_rows: list[DBEvalMatrixResult] = []
    for row in run_result.rows:
        db_row = DBEvalMatrixResult(
            id=f"emr-{uuid.uuid4().hex[:8]}",
            campaign_id=payload.campaign_id,
            defense_combo=row.defense_ids,
            attack_success_rate=row.attack_success_rate,
            benign_pass_rate=row.benign_pass_rate,
            regressions=row.regressions,
            adaptive_asr=row.adaptive_asr,
            static_asr=row.static_asr,
        )
        db.add(db_row)
        db_rows.append(db_row)

    await db.commit()
    for r in db_rows:
        await db.refresh(r)

    return db_rows


@router.get("/matrix/{matrix_id}", response_model=EvalMatrixResponse)
async def get_eval_matrix_row(
    matrix_id: str,
    db: AsyncSession = Depends(get_db),
) -> DBEvalMatrixResult:
    """Retrieve a single matrix row by its ID."""
    stmt = select(DBEvalMatrixResult).where(DBEvalMatrixResult.id == matrix_id)
    res = await db.execute(stmt)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Eval matrix record '{matrix_id}' not found.",
        )
    return row


@router.get("/matrix", response_model=list[EvalMatrixResponse])
async def list_eval_matrix_results(
    campaign_id: Optional[str] = Query(None, description="Campaign ID to filter matrix rows"),
    db: AsyncSession = Depends(get_db),
) -> list[DBEvalMatrixResult]:
    """List evaluation matrix results, optionally filtered by campaign ID."""
    stmt = select(DBEvalMatrixResult).order_by(DBEvalMatrixResult.created_at.desc())
    if campaign_id:
        stmt = stmt.where(DBEvalMatrixResult.campaign_id == campaign_id)
    res = await db.execute(stmt)
    return list(res.scalars().all())

