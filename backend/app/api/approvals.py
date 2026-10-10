"""
API routes for human-in-the-loop approvals.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any
import uuid

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

# In-memory pending approvals store
_pending_approvals: dict[str, dict[str, Any]] = {}

@router.get("/pending")
async def get_pending_approvals() -> list[dict[str, Any]]:
    return list(_pending_approvals.values())

@router.post("/{approval_id}/approve")
async def approve_action(approval_id: str) -> dict[str, str]:
    if approval_id not in _pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")
    _pending_approvals[approval_id]["status"] = "approved"
    return {"status": "approved", "approval_id": approval_id}

@router.post("/{approval_id}/reject")
async def reject_action(approval_id: str) -> dict[str, str]:
    if approval_id not in _pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")
    _pending_approvals[approval_id]["status"] = "rejected"
    return {"status": "rejected", "approval_id": approval_id}
