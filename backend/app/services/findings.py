"""
Findings Management Service.

Upserts discovered findings into the findings table, computes severity scores,
maps root cause keys to OWASP and ATLAS standards, and maintains Wilson 95% CIs.
"""

from __future__ import annotations

import math
import logging
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Finding, FindingEvidence, AttackCorpus

logger = logging.getLogger(__name__)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Calculate Wilson 95% Confidence Interval (ci_low, ci_high)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + (z * z) / n
    center = p + (z * z) / (2.0 * n)
    factor = z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * n)) / n)
    ci_low = max(0.0, (center - factor) / denom)
    ci_high = min(1.0, (center + factor) / denom)
    return (ci_low, ci_high)


def compute_severity_label(score: int) -> str:
    """Calculate severity label from severity_score (impact * exploitability * reach).

    Low: 1-15, Medium: 16-40, High: 41-75, Critical: 76-125
    """
    if score >= 76:
        return "Critical"
    elif score >= 41:
        return "High"
    elif score >= 16:
        return "Medium"
    else:
        return "Low"


MAP_ROOT_CAUSE_TO_OWASP = {
    "instruction_confusion": ("LLM01:2025", "AML.T0051"),
    "canary_leak": ("LLM02:2025", "AML.T0056"),
    "unauthorized_tool_execution": ("LLM06:2025", "AML.T0055"),
    "untrusted_rag_override": ("LLM08:2025", "AML.T0051"),
    "memory_poisoning_trigger": ("LLM01:2025", "AML.T0057"),
    "unbounded_step_consumption": ("LLM10:2025", None),
}


async def upsert_finding_from_attack(
    session: AsyncSession,
    target_version_id: str,
    attack: Any,
    oracle_verdict: dict,
    run_id: str | None = None,
    breaking_seq: int | None = None,
    scenario_id: str | None = None,
    framework_mapping: dict[str, str] | None = None,
) -> Finding:
    """Create or update a finding in the DB from an oracle verdict."""
    root_cause_key = oracle_verdict.get("root_cause_key", "instruction_confusion")
    verdict_type = oracle_verdict.get("verdict", "error")
    is_success = (verdict_type == "success")

    owasp_id = "LLM01:2025"
    atlas_id = "AML.T0051"
    
    if framework_mapping:
        owasp_id = framework_mapping.get("owasp", owasp_id)
        atlas_id = framework_mapping.get("mitre_atlas", atlas_id)
    else:
        owasp_id, atlas_id = MAP_ROOT_CAUSE_TO_OWASP.get(root_cause_key, ("LLM01:2025", "AML.T0051"))

    # Impact, exploitability, reach heuristics
    impact = 4 if verdict_type == "success" else 2
    exploitability = 3
    reach = 3
    severity_score = impact * exploitability * reach
    severity_label = compute_severity_label(severity_score)

    stmt = select(Finding).where(
        Finding.target_version_id == target_version_id,
        Finding.root_cause_key == root_cause_key,
    )
    result = await session.execute(stmt)
    finding = result.scalar_one_or_none()

    if not finding:
        finding = Finding(
            target_version_id=target_version_id,
            root_cause_key=root_cause_key,
            title=f"Vulnerability: {root_cause_key.replace('_', ' ').title()}",
            surface=attack.surface if hasattr(attack, "surface") else "instructions",
            root_cause=f"Oracle proved exploitability via strategy '{getattr(attack, 'strategy', 'direct')}'",
            impact=impact,
            exploitability=exploitability,
            reach=reach,
            severity_score=severity_score,
            severity=severity_label,
            owasp_id=owasp_id,
            atlas_id=atlas_id,
            reliability_k=1 if is_success else 0,
            reliability_n=1,
            breaking_event_seq=breaking_seq,
            status="open" if is_success else "mitigated",
        )
        ci_low, ci_high = wilson_ci(finding.reliability_k, finding.reliability_n)
        finding.ci_low = ci_low
        finding.ci_high = ci_high
        session.add(finding)
        await session.flush()
    else:
        finding.reliability_n += 1
        if is_success:
            finding.reliability_k += 1
            finding.status = "open"
        ci_low, ci_high = wilson_ci(finding.reliability_k, finding.reliability_n)
        finding.ci_low = ci_low
        finding.ci_high = ci_high

    # Add evidence entry if run_id provided
    if run_id and breaking_seq is not None:
        ev = FindingEvidence(finding_id=finding.id, run_id=run_id, event_seq=breaking_seq)
        session.add(ev)

    # Add to attack corpus if successful
    if is_success:
        corpus_entry = AttackCorpus(
            finding_id=finding.id,
            minimized_payload={"goal": attack.goal, "payload": attack.payload},
            active=True,
        )
        session.add(corpus_entry)

    await session.commit()
    return finding


class FindingsService:
    def __init__(self) -> None:
        self.findings: list[dict[str, Any]] = []
        
    def record_finding(self, campaign_id: str, attack_id: str, severity: str, details: dict[str, Any], scenario_id: str | None = None, framework_mapping: dict[str, str] | None = None) -> str:
        finding_id = str(uuid.uuid4())
        self.findings.append({
            "id": finding_id,
            "campaign_id": campaign_id,
            "attack_id": attack_id,
            "severity": severity,
            "details": details,
            "scenario_id": scenario_id,
            "framework_mapping": framework_mapping or {}
        })
        return finding_id
        
    def get_findings_for_campaign(self, campaign_id: str) -> list[dict[str, Any]]:
        return [f for f in self.findings if f["campaign_id"] == campaign_id]


findings_service = FindingsService()

