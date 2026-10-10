"""
API routes for model/prompt validation experiments.
"""
from __future__ import annotations
from fastapi import APIRouter
from typing import Any
from app.services.validation import validation_service

router = APIRouter(prefix="/api/validation", tags=["validation"])

@router.get("/experiments")
async def list_experiments() -> dict[str, Any]:
    return {"experiments": validation_service.experiments}

@router.post("/experiments")
async def create_experiment(payload: dict[str, Any]) -> dict[str, str]:
    exp_id = validation_service.create_experiment(
        payload.get("name", "Unknown"), 
        payload.get("variants", [])
    )
    return {"experiment_id": exp_id}
