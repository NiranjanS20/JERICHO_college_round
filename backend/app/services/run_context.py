"""
RunContext service for AgentBreak.

Provides a unified execution context for simulation runs, bundling campaign,
target agent, attack plan, defenses, oracle, and sandbox configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.defenses.base import Defense
from app.traces.recorder import TraceRecorder


@dataclass
class RunContext:
    """Unified runtime context for a simulation execution."""

    campaign_id: str
    case_study_id: str | None = None
    scenario_id: str | None = None
    caller_role: str = "employee"
    allowed_tools: list[str] | None = None
    victim_model: str | None = None
    injection_point: str | None = None
    defenses: list[Defense] = field(default_factory=list)
    budget_k: int = 5
    max_agent_steps: int = 8
    target_version_id: str = "a0000000-0000-0000-0000-000000000101"
    config_hash: str | None = None
    execution_mode: str = "offline"
    simulation_config: dict[str, Any] = field(default_factory=dict)
    recorder: TraceRecorder | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_simulation_config(
        cls,
        campaign_id: str,
        config: dict[str, Any],
        defenses: list[Defense] | None = None,
        execution_mode: str = "offline",
    ) -> RunContext:
        """Factory method constructing RunContext from an effective simulation config dictionary."""
        from app.defenses import DEFENSE_REGISTRY

        target_cfg = config.get("target", {})
        attack_plan = config.get("attack_plan", {})
        budget_cfg = config.get("budget", {})
        defenses_cfg = config.get("defenses", {})

        instantiated_defenses = defenses or [
            DEFENSE_REGISTRY[d_id]()
            for d_id in defenses_cfg.get("enabled_ids", [])
            if d_id in DEFENSE_REGISTRY
        ]

        return cls(
            campaign_id=campaign_id,
            case_study_id=config.get("case_study_id"),
            scenario_id=attack_plan.get("scenario_id"),
            caller_role=target_cfg.get("caller_role", "employee"),
            allowed_tools=target_cfg.get("enabled_tools"),
            victim_model=target_cfg.get("model_id"),
            injection_point=attack_plan.get("injection_point"),
            defenses=instantiated_defenses,
            budget_k=budget_cfg.get("max_attempts_per_goal", 5),
            max_agent_steps=budget_cfg.get("max_agent_steps", 8),
            target_version_id=target_cfg.get("version_id", "a0000000-0000-0000-0000-000000000101"),
            config_hash=config.get("config_sha256"),
            execution_mode=execution_mode,
            simulation_config=config,
        )
