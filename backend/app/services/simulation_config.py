"""
Simulation Configuration Resolver and Preflight Validator.
Produces an immutable, canonical, fingerprinted run configuration.
Ensures that the UI configuration is the exact configuration executed.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from app.schemas import (
    SimulationConfig,
    PreLaunchCheck,
    PreLaunchValidationResponse,
)
from app.scenarios.case_studies import CASE_STUDIES, CaseStudyDefinition
from app.scenarios.builtin import BUILTIN_SCENARIOS
from app.scenarios.catalogue import ScenarioDefinition
from app.victim.tools import TOOL_REGISTRY
from app.defenses import DEFENSE_REGISTRY
from app.llm.gemini import GeminiClient


def compute_config_hash(data: dict[str, Any]) -> str:
    """Deterministic canonical SHA-256 fingerprint of any configuration dictionary."""
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"


@dataclass
class ResolvedSimulationContext:
    valid: bool
    config_hash: str
    effective_config: dict[str, Any]
    checks: list[PreLaunchCheck]
    warnings: list[str]
    case_study: CaseStudyDefinition | None
    scenario: ScenarioDefinition | None


class SimulationConfigResolver:
    """Canonical resolver and validator for SimulationConfig."""

    @classmethod
    def resolve_and_validate(cls, config: SimulationConfig) -> ResolvedSimulationContext:
        checks: list[PreLaunchCheck] = []
        warnings: list[str] = []

        # 1. Resolve Case Study
        cs_id = config.case_study_id or "customer_support_prompt_injection_v1"
        case_study = next((c for c in CASE_STUDIES if c.id == cs_id), None)
        if not case_study:
            checks.append(PreLaunchCheck(
                name="Case Study",
                passed=False,
                message=f"Case study '{cs_id}' not found in registry.",
            ))
        else:
            version_match = (config.case_study_version is None) or (config.case_study_version == case_study.version)
            if not version_match:
                checks.append(PreLaunchCheck(
                    name="Case Study",
                    passed=False,
                    message=f"Case study '{cs_id}' version mismatch. Expected {case_study.version}, got {config.case_study_version}.",
                ))
            else:
                checks.append(PreLaunchCheck(
                    name="Case Study",
                    passed=True,
                    message=f"Case Study '{case_study.name}' (v{case_study.version}) resolved.",
                ))

        # 2. Resolve Scenario
        scen_id = config.attack_plan.scenario_id or (case_study.default_scenario_id if case_study else "SCEN-001")
        scenario = next((s for s in BUILTIN_SCENARIOS if s.id == scen_id), None)
        if scenario:
            if case_study and scen_id not in case_study.scenario_ids:
                checks.append(PreLaunchCheck(
                    name="Scenario Alignment",
                    passed=False,
                    message=f"Scenario '{scen_id}' does not belong to case study '{cs_id}'.",
                ))
            else:
                checks.append(PreLaunchCheck(
                    name="Scenario Success Criteria",
                    passed=True,
                    message=f"Scenario '{scenario.name}' bound to rule: '{scenario.pass_fail_rule[:65]}...'",
                ))
        else:
            # Custom objective
            checks.append(PreLaunchCheck(
                name="Scenario Success Criteria",
                passed=True,
                message="Custom objective bound to deterministic Oracle evaluator.",
            ))

        # 3. Validate Tools
        enabled_tools = list(config.target.enabled_tools)
        if not enabled_tools and case_study:
            enabled_tools = list(case_study.available_tool_ids)

        unknown_tools = [t for t in enabled_tools if t not in TOOL_REGISTRY]
        if unknown_tools:
            checks.append(PreLaunchCheck(
                name="Tool Registry",
                passed=False,
                message=f"Tools not registered in runtime: {', '.join(unknown_tools)}",
            ))
        elif case_study:
            disallowed_tools = [t for t in enabled_tools if t not in case_study.available_tool_ids]
            if disallowed_tools:
                checks.append(PreLaunchCheck(
                    name="Tool Permissions",
                    passed=False,
                    message=f"Tools not permitted for case study '{case_study.name}': {', '.join(disallowed_tools)}",
                ))
            else:
                checks.append(PreLaunchCheck(
                    name="Tool Registry",
                    passed=True,
                    message=f"All {len(enabled_tools)} tools verified and permitted for {case_study.name}.",
                ))
        else:
            checks.append(PreLaunchCheck(
                name="Tool Registry",
                passed=True,
                message=f"All {len(enabled_tools)} tools verified in runtime.",
            ))

        # 4. Validate Defenses
        enabled_defense_ids = list(config.defenses.enabled_ids)
        unknown_defenses = [d for d in enabled_defense_ids if d not in DEFENSE_REGISTRY]
        if unknown_defenses:
            checks.append(PreLaunchCheck(
                name="Defense Registry",
                passed=False,
                message=f"Defenses not found in registry: {', '.join(unknown_defenses)}",
            ))
        elif case_study:
            missing_required = [d for d in case_study.required_defenses if d not in enabled_defense_ids]
            if missing_required:
                checks.append(PreLaunchCheck(
                    name="Required Defenses",
                    passed=False,
                    message=f"Case study requires defenses that are disabled: {', '.join(missing_required)}",
                ))
            else:
                checks.append(PreLaunchCheck(
                    name="Defense Pipeline",
                    passed=True,
                    message=f"All required defenses ({', '.join(case_study.required_defenses)}) are active.",
                ))
        else:
            checks.append(PreLaunchCheck(
                name="Defense Pipeline",
                passed=True,
                message=f"Defenses validated: {', '.join(enabled_defense_ids) if enabled_defense_ids else 'baseline (none)'}",
            ))

        # 5. Validate Model & Connectivity Mode
        client = GeminiClient.get_instance()
        target_model = config.target.model_id or "gemini-3.8-flash"
        is_live = client.is_configured()
        checks.append(PreLaunchCheck(
            name="Model & Execution Mode",
            passed=True,
            message=f"Target model '{target_model}' configured in {'LIVE' if is_live else 'OFFLINE (deterministic fallback)'} mode.",
        ))

        # 6. Sandbox & Side-effect Isolation
        is_isolated = not config.sandbox.external_network and not config.sandbox.real_side_effects
        checks.append(PreLaunchCheck(
            name="Network & Sandbox Isolation",
            passed=is_isolated,
            message="Sandbox isolated: 0 external network, 0 production side effects." if is_isolated else "WARNING: External network or real side effects enabled.",
        ))

        # Synthetic Fixture Profile validation
        fixture_profile = config.sandbox.fixture_profile_id or (case_study.fixture_profile_id if case_study else "support-demo-v1")
        valid_fixtures = {"support-demo-v1", "hr-demo-v1", "itops-demo-v1"}
        fixture_ok = fixture_profile in valid_fixtures
        checks.append(PreLaunchCheck(
            name="Synthetic Fixture Profile",
            passed=fixture_ok,
            message=f"Synthetic fixture profile '{fixture_profile}' validated." if fixture_ok else f"Unknown fixture profile '{fixture_profile}'.",
        ))

        # 7. Bound Resource Limits
        bounded_attempts = min(max(1, config.budget.max_attempts_per_goal), 10)
        bounded_steps = min(max(1, config.budget.max_agent_steps), 20)
        bounded_llm_calls = min(max(5, config.budget.max_total_llm_calls), 200)
        bounded_wall_seconds = min(max(10, config.budget.max_wall_seconds), 600)

        checks.append(PreLaunchCheck(
            name="Execution Limits",
            passed=True,
            message=f"Enforced limits: {bounded_attempts} attempts, {bounded_steps} steps, {bounded_llm_calls} LLM calls, {bounded_wall_seconds}s timeout.",
        ))

        # Build Canonical Effective Config
        effective_config = config.model_dump()
        effective_config["case_study_id"] = cs_id
        if case_study:
            effective_config["case_study_version"] = case_study.version
            effective_config["case_study_name"] = case_study.name
        effective_config["target"]["enabled_tools"] = enabled_tools
        effective_config["budget"]["max_attempts_per_goal"] = bounded_attempts
        effective_config["budget"]["max_agent_steps"] = bounded_steps
        effective_config["budget"]["max_total_llm_calls"] = bounded_llm_calls
        effective_config["budget"]["max_wall_seconds"] = bounded_wall_seconds

        config_hash = compute_config_hash(effective_config)
        effective_config["config_sha256"] = config_hash

        all_passed = all(c.passed for c in checks)

        return ResolvedSimulationContext(
            valid=all_passed,
            config_hash=config_hash,
            effective_config=effective_config,
            checks=checks,
            warnings=warnings,
            case_study=case_study,
            scenario=scenario,
        )
