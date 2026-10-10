"""
API routes for model/prompt validation experiments and statistical benchmark suites.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, status
from typing import Any
from pydantic import BaseModel, Field
from app.services.validation import validation_service

router = APIRouter(prefix="/api/validation", tags=["validation"])


class CreateExperimentPayload(BaseModel):
    name: str = Field(..., description="Descriptive title of the benchmark experiment")
    category: str = Field("defense_ab", description="Category: defense_ab | adaptive_vs_static | utility_retention | regression_gate")
    goal: str = Field("Exfiltrate canary secret or test system prompt", description="Target objective or threat scenario")
    threat_model: str = Field("OWASP LLM01: Prompt Injection", description="Security framework mapping")
    variants: list[str] = Field(default_factory=list, description="List of candidate configurations or defensive layers")
    replications: int = Field(10, ge=2, le=50, description="Number of Monte Carlo empirical replications")


@router.get("/experiments")
async def list_experiments() -> dict[str, Any]:
    """Retrieve all benchmark and validation experiments."""
    return {
        "experiments": validation_service.experiments,
        "count": len(validation_service.experiments),
    }


@router.get("/experiments/{exp_id}")
async def get_experiment(exp_id: str) -> dict[str, Any]:
    """Retrieve detailed telemetry for a specific experiment."""
    exp = validation_service.get_experiment(exp_id)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{exp_id}' not found.",
        )
    return exp


@router.post("/experiments", status_code=status.HTTP_201_CREATED)
async def create_experiment(payload: CreateExperimentPayload) -> dict[str, Any]:
    """Launch a new validation experiment with automated statistical evaluation."""
    exp_id = validation_service.create_experiment(
        name=payload.name,
        category=payload.category,
        goal=payload.goal,
        variants_input=payload.variants,
        replications=payload.replications,
        threat_model=payload.threat_model,
    )
    return {
        "experiment_id": exp_id,
        "experiment": validation_service.get_experiment(exp_id),
        "status": "created",
    }


@router.delete("/experiments/{exp_id}")
async def delete_experiment(exp_id: str) -> dict[str, bool]:
    """Delete an experiment."""
    deleted = validation_service.delete_experiment(exp_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{exp_id}' not found.",
        )
    return {"deleted": True}
