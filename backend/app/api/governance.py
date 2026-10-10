"""
Governance API (GOV-03).
Maps components to owners for accountability.
Allows viewing for Owners, Auditors, and Safety Leads.
Allows reassigning owners for Safety Leads only.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Any
from pydantic import BaseModel
from app.security.rbac import require_permission
from app.security.auth import Principal

router = APIRouter(prefix="/api/governance", tags=["governance"])

COMPONENT_OWNERS: dict[str, str] = {
    "sys-prompt": "ai-safety-team",
    "policy-engine": "sec-eng",
    "tool-send_email": "core-services",
    "tool-write_memory": "core-services",
    "gemini-client": "ai-platform",
}

class OwnerUpdate(BaseModel):
    owner: str

@router.get("/owners")
async def list_owners(
    _principal: Principal = Depends(require_permission("view_governance")),
) -> list[dict[str, str]]:
    return [{"component": k, "owner": v} for k, v in COMPONENT_OWNERS.items()]

@router.put("/owners/{component}")
async def update_component_owner(
    component: str,
    payload: OwnerUpdate,
    _principal: Principal = Depends(require_permission("edit_governance")),
) -> dict[str, str]:
    COMPONENT_OWNERS[component] = payload.owner
    return {"component": component, "owner": payload.owner, "status": "updated"}
