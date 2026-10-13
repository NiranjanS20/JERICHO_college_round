"""
Campaign API routes for AgentBreak.

Handles creating campaigns, triggering background red-team runs with SSE
broadcasting, persisting findings, and querying campaign execution state.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.llm.gemini import GeminiClient
from app.db import get_db, async_session_factory
from app.models import Attack, Campaign, TraceStep
from app.schemas import (
    CampaignCreate,
    CampaignResponse,
    SimulationConfig,
    PreLaunchValidationResponse,
    PreLaunchCheck,
)
from app.services.event_bus import event_bus
from app.services.findings import upsert_finding_from_attack
from app.victim.agent import VictimAgent
from app.victim.tools import TOOL_REGISTRY
from app.scenarios.builtin import BUILTIN_SCENARIOS
from app.scenarios.case_studies import CASE_STUDIES
from app.attacker.engine import AdaptiveAttackEngine
from app.defenses import DEFENSE_REGISTRY

from app.security.rbac import require_permission
from app.security.auth import Principal

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


def compute_config_hash(data: dict[str, Any]) -> str:
    """Canonicalize dictionary and compute deterministic SHA-256 fingerprint."""
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"


async def _run_campaign_worker(
    campaign_id: str,
    goals: list[str],
    categories: list[str],
    budget_per_goal: int,
    defense_ids: list[str],
    simulation_config: dict[str, Any] | None = None,
) -> None:
    """Background worker executing adaptive attack runs, persisting all attempts, and streaming events."""
    # Validate defenses
    unknown = [d_id for d_id in defense_ids if d_id not in DEFENSE_REGISTRY]
    if unknown:
        raise ValueError(f"Unknown defense IDs specified: {', '.join(unknown)}")

    defenses = [DEFENSE_REGISTRY[d_id]() for d_id in defense_ids]
    engine = AdaptiveAttackEngine()
    gemini = GeminiClient.get_instance()
    execution_mode = "live" if (gemini.is_configured and not get_settings().demo_mode) else "offline"

    # Extract scenario execution context from simulation_config
    case_study_id = None
    scenario_id = None
    caller_role = "employee"
    allowed_tools = None
    victim_model = None
    injection_point_override = None
    target_version_id = "a0000000-0000-0000-0000-000000000101"
    config_hash = None

    if simulation_config:
        case_study_id = simulation_config.get("case_study_id")
        config_hash = simulation_config.get("config_sha256")
        target_cfg = simulation_config.get("target", {})
        caller_role = target_cfg.get("caller_role", "employee")
        allowed_tools = target_cfg.get("enabled_tools")
        victim_model = target_cfg.get("model_id")
        target_version_id = target_cfg.get("version_id", target_version_id)

        attack_plan = simulation_config.get("attack_plan", {})
        scenario_id = attack_plan.get("scenario_id")
        injection_point_override = attack_plan.get("injection_point")

    total_attempts = 0

    async with async_session_factory() as db:
        for goal_idx, goal in enumerate(goals):
            atk_id = f"atk-{uuid.uuid4().hex[:8]}"
            await event_bus.publish(
                campaign_id,
                {
                    "event": "attack_started",
                    "attack_id": atk_id,
                    "campaign_id": campaign_id,
                    "goal": goal,
                    "strategy": "adaptive_search",
                    "iteration": 1,
                    "case_study_id": case_study_id,
                    "scenario_id": scenario_id,
                    "execution_mode": execution_mode,
                },
            )

            # Iteration callback publishing real-time attempt progress to SSE
            async def _on_iteration_step(step_data: dict[str, Any]) -> None:
                await event_bus.publish(
                    campaign_id,
                    {
                        "event": "iteration_completed",
                        "campaign_id": campaign_id,
                        "attack_id": atk_id,
                        "iteration": step_data.get("iteration"),
                        "strategy": step_data.get("strategy"),
                        "injection_point": step_data.get("injection_point"),
                        "score": step_data.get("score"),
                        "success": step_data.get("success"),
                        "verdict": step_data.get("verdict"),
                        "oracle_success": step_data.get("oracle_success"),
                        "tool_calls_count": step_data.get("tool_calls_count"),
                        "execution_mode": execution_mode,
                    },
                )

            # Run adaptive discovery loop with explicit run context
            result = await engine.execute_goal(
                goal=goal,
                category=categories[goal_idx] if goal_idx < len(categories) else (categories[0] if categories else "LLM01: Prompt Injection"),
                budget_k=budget_per_goal,
                defenses=defenses,
                on_step_callback=_on_iteration_step,
                case_study_id=case_study_id,
                scenario_id=scenario_id,
                caller_role=caller_role,
                allowed_tools=allowed_tools,
                victim_model=victim_model,
                injection_point_override=injection_point_override,
            )

            total_attempts += len(result.history)
            best_verdict_dict = None
            primary_attack_record = None

            # Load campaign object in session with attacks relationship eagerly loaded
            camp_res = await db.execute(
                select(Campaign)
                .options(selectinload(Campaign.attacks))
                .where(Campaign.id == campaign_id)
            )
            camp_obj = camp_res.scalar_one_or_none()

            try:
                for att in result.history:
                    att_id = f"{atk_id}-i{att.iteration}"
                    v = att.verdict
                    verdict_dict = {
                        "success": v.success,
                        "verdict": v.verdict,
                        "root_cause_key": v.root_cause_key,
                        "violated_policies": v.violated_policies,
                        "severity": v.severity,
                        "evidence": v.evidence,
                        "partial_score": v.partial_score,
                        "details": v.details,
                        "execution_status": v.execution_status,
                    }
                    if att.best_in_chain:
                        best_verdict_dict = verdict_dict

                    attempt_status = "success" if v.success else "failure"

                    db_attempt = Attack(
                        id=att_id,
                        campaign_id=campaign_id,
                        goal=goal,
                        category=categories[goal_idx] if goal_idx < len(categories) else (categories[0] if categories else "prompt_injection"),
                        strategy=att.strategy,
                        iteration=att.iteration,
                        injection_point=att.injection_point,
                        payload={"text": att.payload},
                        verdict=v.verdict,
                        status=attempt_status,
                        oracle_verdict=verdict_dict,
                        partial_score=att.score,
                        best_in_chain=att.best_in_chain,
                        execution_mode=execution_mode,
                        config_hash=config_hash,
                    )
                    if camp_obj is not None:
                        camp_obj.attacks.append(db_attempt)
                    else:
                        db.add(db_attempt)
                    if att.best_in_chain or primary_attack_record is None:
                        primary_attack_record = db_attempt

                await db.flush()
            except Exception as loop_exc:
                import traceback
                print(f"DEBUG WORKER ERROR DURING PERSISTENCE: {loop_exc}")
                traceback.print_exc()

            # Save trace recorder steps and hash chain to DB
            if result.recorder and primary_attack_record:
                result.recorder.attack_id = primary_attack_record.id
                result.recorder.run_id = primary_attack_record.id
                await result.recorder.save_to_db(db)

            # Upsert finding into DB if oracle verdict exists
            if best_verdict_dict and primary_attack_record:
                await upsert_finding_from_attack(
                    session=db,
                    target_version_id=target_version_id,
                    attack=primary_attack_record,
                    oracle_verdict=best_verdict_dict,
                    run_id=primary_attack_record.id,
                    breaking_seq=len(result.recorder._steps) if result.recorder else 0,
                )

                await event_bus.publish(
                    campaign_id,
                    {
                        "event": "oracle_verdict",
                        "attack_id": atk_id,
                        "verdict": best_verdict_dict,
                    },
                )

            final_attack_status = "success" if (best_verdict_dict and best_verdict_dict["success"]) else "failure"
            await event_bus.publish(
                campaign_id,
                {
                    "event": "attack_finished",
                    "attack_id": atk_id,
                    "status": final_attack_status,
                    "partial_score": result.best_score,
                    "oracle_verdict": best_verdict_dict,
                    "total_iterations": result.total_iterations,
                    "execution_mode": execution_mode,
                },
            )

        # Update campaign status to completed
        res = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        c = res.scalar_one_or_none()
        if c:
            c.status = "completed"
            c.attempts_used = total_attempts
            c.ended_at = datetime.now(timezone.utc)
            c.execution_mode = execution_mode
            c.llm_calls_used = sum(gemini.call_counts.values()) if gemini.is_configured else 0
        await db.commit()

        await event_bus.publish(
            campaign_id,
            {
                "event": "campaign_finished",
                "campaign_id": campaign_id,
                "status": "completed",
                "attempts_used": total_attempts,
                "execution_mode": execution_mode,
            },
        )


@router.post("/validate", response_model=PreLaunchValidationResponse)
async def validate_simulation(
    payload: SimulationConfig,
    _principal: Principal = Depends(require_permission("launch_campaign")),
) -> PreLaunchValidationResponse:
    """Pre-launch validation checklist ensuring safety, criteria, limits, and frozen snapshot."""
    from app.services.simulation_config import SimulationConfigResolver
    resolved = SimulationConfigResolver.resolve_and_validate(payload)
    return PreLaunchValidationResponse(
        valid=resolved.valid,
        config_hash=resolved.config_hash,
        checks=resolved.checks,
        effective_config=resolved.effective_config,
        warnings=resolved.warnings,
    )


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    _principal: Principal = Depends(require_permission("launch_campaign")),
) -> Campaign:
    """Create a new campaign and start background attack discovery."""
    goals = payload.goals
    categories = payload.categories
    budget_per_goal = payload.budget_per_goal
    defense_ids = payload.defense_ids
    snapshot = dict(payload.config_snapshot or {})

    sim_cfg_dict = None
    if payload.simulation_config:
        from app.services.simulation_config import SimulationConfigResolver
        resolved = SimulationConfigResolver.resolve_and_validate(payload.simulation_config)
        if not resolved.valid:
            failed_msgs = [c.message for c in resolved.checks if not c.passed]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Preflight validation failed: {'; '.join(failed_msgs)}",
            )
        sim_cfg_dict = resolved.effective_config
        goals = [payload.simulation_config.attack_plan.goal]
        categories = [payload.simulation_config.attack_plan.category]
        budget_per_goal = sim_cfg_dict["budget"]["max_attempts_per_goal"]
        defense_ids = sim_cfg_dict["defenses"]["enabled_ids"]

        snapshot.update(sim_cfg_dict)
        snapshot["config_sha256"] = resolved.config_hash
        snapshot["case_study_id"] = sim_cfg_dict.get("case_study_id")
        snapshot["scenario_id"] = sim_cfg_dict["attack_plan"]["scenario_id"]
        snapshot["injection_point"] = sim_cfg_dict["attack_plan"]["injection_point"]
        snapshot["target_version"] = sim_cfg_dict["target"]["version_id"]
    else:
        # Validate defenses if provided manually
        unknown = [d for d in defense_ids if d not in DEFENSE_REGISTRY]
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown defense IDs: {', '.join(unknown)}",
            )
        if not snapshot.get("config_sha256"):
            snapshot["config_sha256"] = compute_config_hash({
                "goals": goals,
                "categories": categories,
                "budget": budget_per_goal,
                "defense_ids": defense_ids,
            })

    gemini = GeminiClient.get_instance()
    exec_mode = "live" if (gemini.is_configured and not get_settings().demo_mode) else "offline"
    now_utc = datetime.now(timezone.utc)

    campaign = Campaign(
        id=f"camp-{uuid.uuid4().hex[:8]}",
        status="running",
        goals=goals,
        categories=categories or ["prompt_injection"],
        budget_per_goal=budget_per_goal,
        defense_ids=defense_ids or [],
        config_snapshot=snapshot,
        provenance=payload.provenance,
        execution_mode=exec_mode,
        started_at=now_utc,
    )

    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    camp_id = campaign.id

    # Publish campaign_started event to buffer
    await event_bus.publish(
        camp_id,
        {
            "event": "campaign_started",
            "campaign_id": camp_id,
            "goals": goals,
            "config_hash": snapshot.get("config_sha256"),
            "case_study_id": snapshot.get("case_study_id"),
            "execution_mode": exec_mode,
        },
    )

    # Launch background worker safely
    async def _safe_worker() -> None:
        try:
            await _run_campaign_worker(
                campaign_id=camp_id,
                goals=goals,
                categories=categories,
                budget_per_goal=budget_per_goal,
                defense_ids=defense_ids,
                simulation_config=sim_cfg_dict,
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            await event_bus.publish(camp_id, {"event": "campaign_failed", "campaign_id": camp_id, "error": str(e)})
            async with async_session_factory() as async_db:
                res = await async_db.execute(select(Campaign).where(Campaign.id == camp_id))
                c = res.scalar_one_or_none()
                if c:
                    c.status = "failed"
                    c.ended_at = datetime.now(timezone.utc)
                await async_db.commit()
            await event_bus.publish(camp_id, {"event": "campaign_finished", "campaign_id": camp_id, "status": "failed"})

    asyncio.create_task(_safe_worker())

    return campaign


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
) -> list[Campaign]:
    """Retrieve all campaigns ordered by creation date."""
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
) -> Campaign:
    """Retrieve details for a specific campaign."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign '{campaign_id}' not found.",
        )
    return campaign


@router.post("/{campaign_id}/benign")
async def run_campaign_benign_tasks(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    _principal: Principal = Depends(require_permission("launch_campaign")),
) -> dict[str, Any]:
    """Execute legitimate benign workflow tasks against the campaign's target configuration to verify utility."""
    from app.services.benign_runner import BenignTaskRunner
    from app.defenses import DEFENSE_REGISTRY

    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign '{campaign_id}' not found.",
        )

    snapshot = campaign.config_snapshot or {}
    case_study_id = snapshot.get("case_study_id") or "customer_support_prompt_injection_v1"
    target_cfg = snapshot.get("target", {})
    caller_role = target_cfg.get("caller_role", "employee")
    allowed_tools = target_cfg.get("enabled_tools")
    victim_model = target_cfg.get("model_id")

    defense_ids = campaign.defense_ids or []
    defenses = [DEFENSE_REGISTRY[d_id]() for d_id in defense_ids if d_id in DEFENSE_REGISTRY]

    runner = BenignTaskRunner()
    summary = await runner.run_for_case_study(
        case_study_id=case_study_id,
        defenses=defenses,
        caller_role=caller_role,
        allowed_tools=allowed_tools,
        model=victim_model,
    )

    return {
        "campaign_id": campaign_id,
        "case_study_id": case_study_id,
        "total_tasks": summary.total_tasks,
        "passed_tasks": summary.passed_tasks,
        "utility_rate": summary.utility_rate,
        "results": summary.results,
    }
