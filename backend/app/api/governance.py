"""
Governance API (GOV-03).
Maps components to owners for accountability.
"""
from fastapi import APIRouter
from typing import Any

router = APIRouter(prefix="/api/governance", tags=["governance"])

COMPONENT_OWNERS = {
    "sys-prompt": "ai-safety-team",
    "policy-engine": "sec-eng",
    "tool-send_email": "core-services",
    "tool-write_memory": "core-services",
    "gemini-client": "ai-platform",
}

@router.get("/owners")
async def list_owners() -> list[dict[str, str]]:
    return [{"component": k, "owner": v} for k, v in COMPONENT_OWNERS.items()]
