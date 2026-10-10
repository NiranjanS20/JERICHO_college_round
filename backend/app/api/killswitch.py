"""
Kill Switch API (INC-01).
Provides campaign-level Emergency Stop (Analyst & Safety Lead)
and Global Kill Switch trigger/reset (Safety Lead only).
"""
from fastapi import APIRouter, Depends, Query
from typing import Any
from app.security.kill_switch import KillSwitch
from app.security.rbac import require_permission
from app.security.auth import Principal

router = APIRouter(tags=["killswitch"])

@router.post("/api/campaigns/{campaign_id}/kill")
async def kill_campaign(
    campaign_id: str,
    _principal: Principal = Depends(require_permission("emergency_stop")),
) -> dict[str, str]:
    """Emergency stop for a specific running campaign (Analyst or Safety Lead)."""
    KillSwitch.kill(campaign_id)
    return {"status": "killed", "campaign_id": campaign_id}

@router.get("/api/killswitch/status")
async def get_killswitch_status() -> dict[str, Any]:
    """Retrieve current state of the global kill switch."""
    return KillSwitch.get_global_status()

@router.post("/api/killswitch/trigger")
async def trigger_global_killswitch(
    reason: str = Query("Safety Lead initiated platform-wide emergency stop"),
    _principal: Principal = Depends(require_permission("kill_switch_trigger")),
) -> dict[str, Any]:
    """Platform-wide emergency halt of all running campaigns (Safety Lead only)."""
    KillSwitch.trigger_global(reason=reason)
    return {"status": "triggered", "reason": reason}

@router.post("/api/killswitch/reset")
async def reset_global_killswitch(
    _principal: Principal = Depends(require_permission("kill_switch_reset")),
) -> dict[str, Any]:
    """Reset the global kill switch back to normal operations (Safety Lead only)."""
    KillSwitch.reset_global()
    return {"status": "reset", "active": False}
