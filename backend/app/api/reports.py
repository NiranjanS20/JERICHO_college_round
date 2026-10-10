"""
Report API routes for AgentBreak.

Provides automated export of campaign findings in structured JSON
and print-ready HTML/PDF formats.
"""

from __future__ import annotations

from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Campaign
from app.reports.export import export_campaign_html, export_campaign_json

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{campaign_id}")
async def get_campaign_report(
    campaign_id: str,
    format: Literal["json", "pdf", "html"] = Query("json", description="Output format"),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a comprehensive security assessment report."""
    from app.models import Attack
    stmt = (
        select(Campaign)
        .options(
            selectinload(Campaign.attacks).selectinload(Attack.trace_steps),
            selectinload(Campaign.eval_matrix_results),
        )
        .where(Campaign.id == campaign_id)
    )
    res = await db.execute(stmt)
    campaign = res.scalar_one_or_none()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign '{campaign_id}' not found.",
        )

    if format == "json":
        return JSONResponse(content=export_campaign_json(campaign))

    # For PDF or HTML, return self-contained printable HTML document
    html_content = export_campaign_html(campaign)
    return HTMLResponse(content=html_content)
