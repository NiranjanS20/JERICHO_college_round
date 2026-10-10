"""
Human approval defense for AgentBreak.

Requires explicit human confirmation for sensitive tools (send_email, write_memory).
In autonomous evaluation and red-team benchmark mode, unapproved sensitive tool calls
are automatically blocked to enforce principle of least privilege.
"""

from __future__ import annotations

from typing import Any

from app.defenses.base import Defense
from app.victim.policy import SENSITIVE_TOOLS


class HumanApprovalDefense(Defense):
    """Enforces human-in-the-loop authorization gates for sensitive tool calls."""

    id = "human_approval"
    name = "Human-in-the-Loop Approval Gate"
    description = (
        "Sensitive side-effect tools (send_email, write_memory) require explicit "
        "human operator approval; auto-denies in automated evaluation mode."
    )

    def __init__(
        self,
        auto_deny_in_eval: bool = True,
        approved_tokens: set[str] | None = None,
        enabled: bool = True,
    ) -> None:
        super().__init__(enabled=enabled)
        self.auto_deny = auto_deny_in_eval
        self.approved_tokens = approved_tokens or set()

    def pre_tool(self, tool_name: str, args: dict[str, Any]) -> tuple[bool, str]:
        """Intercept sensitive tools and require authorization."""
        if tool_name in SENSITIVE_TOOLS:
            # Check if this specific call has an approved token attached
            token = args.get("_approval_token")
            if token and token in self.approved_tokens:
                return True, "Tool call authorized with valid approval token."

            if self.auto_deny:
                return (
                    False,
                    f"Sensitive action {tool_name!r} requires human approval. "
                    "Auto-denied in autonomous evaluation mode.",
                )

        return True, "Tool call permitted."

