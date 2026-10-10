"""
Defenses subsystem for AgentBreak.

Exports all pluggable defense layers and factory helpers to build defense pipelines.
"""

from __future__ import annotations

from app.defenses.base import Defense, DefensePipeline
from app.defenses.delimiting import DelimitingDefense
from app.defenses.hierarchy_prompt import HierarchyPromptDefense
from app.defenses.human_approval import HumanApprovalDefense
from app.defenses.injection_classifier import InjectionClassifierDefense
from app.defenses.policy_engine import PolicyEngineDefense

DEFENSE_REGISTRY: dict[str, type[Defense]] = {
    "delimiting": DelimitingDefense,
    "hierarchy_prompt": HierarchyPromptDefense,
    "policy_engine": PolicyEngineDefense,
    "injection_classifier": InjectionClassifierDefense,
    "human_approval": HumanApprovalDefense,
}


def get_defense(defense_id: str) -> Defense | None:
    """Instantiate a defense by ID."""
    cls = DEFENSE_REGISTRY.get(defense_id)
    return cls() if cls else None


def list_defense_metadata() -> list[dict[str, str]]:
    """Return catalog of available defenses."""
    return [
        {
            "id": cls.id,
            "name": cls.name,
            "description": cls.description,
        }
        for cls in DEFENSE_REGISTRY.values()
    ]


def build_pipeline(defense_ids: list[str]) -> DefensePipeline:
    """Construct an active DefensePipeline from a list of defense IDs."""
    instances: list[Defense] = []
    for d_id in defense_ids:
        d = get_defense(d_id)
        if d:
            instances.append(d)
    return DefensePipeline(instances)


__all__ = [
    "Defense",
    "DefensePipeline",
    "DelimitingDefense",
    "HierarchyPromptDefense",
    "PolicyEngineDefense",
    "InjectionClassifierDefense",
    "HumanApprovalDefense",
    "DEFENSE_REGISTRY",
    "get_defense",
    "list_defense_metadata",
    "build_pipeline",
]

