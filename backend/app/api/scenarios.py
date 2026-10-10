from fastapi import APIRouter
from app.scenarios.builtin import BUILTIN_SCENARIOS
from app.scenarios.case_studies import CASE_STUDIES

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

@router.get("")
async def list_scenarios():
    return [scenario.__dict__ for scenario in BUILTIN_SCENARIOS]

@router.get("/case-studies")
async def list_case_studies():
    return [case_study.__dict__ for case_study in CASE_STUDIES]

