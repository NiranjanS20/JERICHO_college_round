from fastapi import APIRouter
from app.scenarios.builtin import BUILTIN_SCENARIOS

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

@router.get("")
async def list_scenarios():
    return [scenario.__dict__ for scenario in BUILTIN_SCENARIOS]
