"""
Scenario catalogue models.
"""
from __future__ import annotations

from dataclasses import dataclass, field

@dataclass(frozen=True)
class ScenarioDefinition:
    """Definition of an authorized test scenario."""
    id: str
    name: str
    objective: str
    preconditions: list[str]
    permitted_environment: str
    expected_boundary: str
    pass_fail_rule: str
    framework_mapping: dict[str, str] = field(default_factory=dict)
    version: str = "1.0.0"
    owner: str = "security_team"
