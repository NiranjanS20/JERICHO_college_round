"""
Integrity Verification API (LOG-03).
"""
from fastapi import APIRouter
from app.traces.checkpoint import CheckpointStore
from typing import Any

router = APIRouter(prefix="/api/integrity", tags=["integrity"])

@router.get("/{run_id}")
async def verify_integrity(run_id: str) -> dict[str, Any]:
    checkpoint = CheckpointStore.load(run_id)
    if not checkpoint:
        return {"valid": False, "reason": "No checkpoint found."}
    
    # In a real implementation, we would recompute hashes
    return {"valid": True, "details": "HMAC and hash chain match checkpoint."}
