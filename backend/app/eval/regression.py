"""
Regression detector for AgentBreak.

Analyzes changes between two evaluation runs:
- Security Regressions: Attacks previously blocked that now breach policy.
- Utility Regressions: Benign workflows that previously passed but are newly broken
  (false-positive over-defending).
- Security Improvements: Attacks newly mitigated by upgraded defenses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RegressionReport:
    """Detailed diff between two evaluation matrix states."""

    baseline_label: str
    target_label: str
    security_regressions: list[dict[str, Any]] = field(default_factory=list)
    utility_regressions: list[dict[str, Any]] = field(default_factory=list)
    security_improvements: list[dict[str, Any]] = field(default_factory=list)
    utility_improvements: list[dict[str, Any]] = field(default_factory=list)
    has_regressions: bool = False


def detect_regressions(
    baseline_attacks: list[dict[str, Any]],
    target_attacks: list[dict[str, Any]],
    baseline_benign: list[dict[str, Any]],
    target_benign: list[dict[str, Any]],
    baseline_label: str = "Baseline",
    target_label: str = "Target",
) -> RegressionReport:
    """Compare two sets of attack and benign results to identify regressions."""
    report = RegressionReport(
        baseline_label=baseline_label,
        target_label=target_label,
    )

    # 1. Compare attacks
    baseline_att_map = {a.get("id"): a for a in baseline_attacks if "id" in a}
    for t_att in target_attacks:
        att_id = t_att.get("id")
        if not att_id or att_id not in baseline_att_map:
            continue
        b_att = baseline_att_map[att_id]

        b_success = b_att.get("success", False)
        t_success = t_att.get("success", False)

        # Attack was blocked in baseline, but now succeeds in target -> Security Regression!
        if (not b_success) and t_success:
            report.security_regressions.append({
                "id": att_id,
                "name": t_att.get("name", att_id),
                "category": t_att.get("category", "unknown"),
                "detail": "Previously blocked attack now succeeds.",
            })

        # Attack succeeded in baseline, but is now blocked in target -> Improvement!
        elif b_success and (not t_success):
            report.security_improvements.append({
                "id": att_id,
                "name": t_att.get("name", att_id),
                "category": t_att.get("category", "unknown"),
                "detail": "Previously successful attack is now blocked.",
            })

    # 2. Compare benign tasks
    baseline_benign_map = {b.get("task_id"): b for b in baseline_benign if "task_id" in b}
    for t_b in target_benign:
        task_id = t_b.get("task_id")
        if not task_id or task_id not in baseline_benign_map:
            continue
        b_b = baseline_benign_map[task_id]

        b_passed = b_b.get("passed", False)
        t_passed = t_b.get("passed", False)

        # Benign task passed in baseline, but now fails in target -> Utility Regression!
        if b_passed and (not t_passed):
            report.utility_regressions.append({
                "task_id": task_id,
                "name": t_b.get("name", task_id),
                "reason": t_b.get("reason", "Unknown failure"),
                "detail": "Legitimate workflow newly broken by defenses.",
            })

        elif (not b_passed) and t_passed:
            report.utility_improvements.append({
                "task_id": task_id,
                "name": t_b.get("name", task_id),
                "detail": "Previously broken benign task now functions properly.",
            })

    report.has_regressions = (
        len(report.security_regressions) > 0 or len(report.utility_regressions) > 0
    )
    return report

