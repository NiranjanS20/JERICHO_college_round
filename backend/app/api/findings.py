"""
API routes for vulnerability findings.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from typing import Any

from app.security.auth import get_principal, Principal
from app.services.findings import findings_service

router = APIRouter(prefix="/api/findings", tags=["findings"])

@router.get("/{campaign_id}")
async def get_findings(
    campaign_id: str,
    principal: Principal = Depends(get_principal)
) -> list[dict[str, Any]]:
    """Retrieve findings for a specific campaign."""
    return findings_service.get_findings_for_campaign(campaign_id)
