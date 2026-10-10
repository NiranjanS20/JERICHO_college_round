"""
Base defense class and defense pipeline for AgentBreak.

All defenses implement a common interface with pre-LLM, pre-tool,
and post-retrieval interception hooks. The DefensePipeline chains
multiple enabled defenses together in deterministic order.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class Defense(ABC):
    """Abstract base class for all defense layers."""

    id: str
    name: str
    description: str

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def pre_llm(self, messages: list[Any]) -> list[Any]:
        """Inspect or mutate messages before sending to the LLM.

        Can prepend instruction hierarchies or wrap prompts.
        """
        return messages

    def pre_tool(self, tool_name: str, args: dict[str, Any]) -> tuple[bool, str]:
        """Validate a tool call before execution.

        Returns (allowed: bool, reason: str). If allowed is False,
        the tool call is blocked and reason is returned to the agent.
        """
        return True, "Allowed"

    def post_retrieval(self, tool_name: str, result: Any) -> Any:
        """Sanitize or transform content returned from tools (e.g. emails, docs).

        Can wrap untrusted data in delimiting boundaries or strip injections.
        """
        return result


class DefensePipeline:
    """Manages an ordered stack of active defenses."""

    def __init__(self, defenses: list[Defense] | None = None) -> None:
        self.defenses: list[Defense] = defenses or []

    def get_defense_ids(self) -> list[str]:
        """Return list of enabled defense IDs."""
        return [d.id for d in self.defenses if d.enabled]

    def apply_pre_llm(self, messages: list[Any]) -> list[Any]:
        """Run all enabled defenses' pre_llm hooks in sequence."""
        current = list(messages)
        for defense in self.defenses:
            if defense.enabled:
                current = defense.pre_llm(current)
        return current

    def apply_pre_tool(self, tool_name: str, args: dict[str, Any]) -> tuple[bool, str]:
        """Run all enabled defenses' pre_tool hooks.

        Short-circuits on first denial.
        """
        for defense in self.defenses:
            if defense.enabled:
                allowed, reason = defense.pre_tool(tool_name, args)
                if not allowed:
                    return False, f"Blocked by {defense.name} ({defense.id}): {reason}"
        return True, "Allowed"

    def apply_post_retrieval(self, tool_name: str, result: Any) -> Any:
        """Run all enabled defenses' post_retrieval hooks in sequence."""
        current = result
        for defense in self.defenses:
            if defense.enabled:
                current = defense.post_retrieval(tool_name, current)
        return current

