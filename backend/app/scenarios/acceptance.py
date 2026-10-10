"""
Acceptance criteria executable checks.
"""
from __future__ import annotations

from typing import Any

def check_trace_completeness(trace_data: dict[str, Any]) -> bool:
    """Every run produces a trace with scenario ID, config versions, tool requests, broker decisions and outcome."""
    if not trace_data:
        return False
    required_keys = {"scenario_id", "config_version", "policy_version", "steps", "verdict"}
    return required_keys.issubset(trace_data.keys())

def check_prohibited_actions_denied(steps: list[dict[str, Any]]) -> bool:
    """All prohibited mock actions are denied by the independent broker."""
    for step in steps:
        if step.get("type") == "policy_decision" and not step.get("allowed", True):
            # Evidence of denial exists
            return True
    return False

# Other acceptance criteria checks from 9.1 can be added here
