"""
Kill Switch API (INC-01).
"""
from fastapi import APIRouter
from app.security.kill_switch import KillSwitch

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

@router.post("/{campaign_id}/kill")
async def kill_campaign(campaign_id: str) -> dict[str, str]:
    KillSwitch.kill(campaign_id)
    return {"status": "killed", "campaign_id": campaign_id}
