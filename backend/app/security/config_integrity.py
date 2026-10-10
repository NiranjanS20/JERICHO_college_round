"""
Configuration integrity module.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from app.config import get_settings
from app.victim.policy import SYSTEM_PROMPT, POLICY_RULES, ALLOWED_TOOLS

@dataclass
class ConfigSnapshot:
    """Frozen snapshot of the agent configuration."""
    model_name: str
    temperature: float
    system_prompt: str
    policy_rules: list[dict]
    allowed_tools: list[str]
    defense_ids: list[str]

    @property
    def config_version(self) -> str:
        """Return SHA256 hash of the full configuration."""
        data = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @property
    def policy_version(self) -> str:
        """Return SHA256 hash of the policy rules and system prompt."""
        data = json.dumps({"policy_rules": self.policy_rules, "system_prompt": self.system_prompt}, sort_keys=True)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

def create_config_snapshot(defense_ids: list[str] | None = None) -> ConfigSnapshot:
    """Create a snapshot of the current configuration."""
    settings = get_settings()
    return ConfigSnapshot(
        model_name=settings.victim_model,
        temperature=settings.victim_temperature,
        system_prompt=SYSTEM_PROMPT,
        policy_rules=[{ "id": r.id, "description": r.description, "severity": r.severity } for r in POLICY_RULES],
        allowed_tools=sorted(list(ALLOWED_TOOLS)),
        defense_ids=sorted(defense_ids or [])
    )
