"""
Non-LLM deterministic policy engine defense for AgentBreak.

Inspects tool calls before execution in a pure code layer. Enforces:
- Tool allowlists
- Strict @acme.com recipient domains for send_email
- Arguments inspection for canary string leaks
- Customer PII data export restrictions
- Suspicious memory key blocks
"""

from __future__ import annotations

import re
from typing import Any

from app.defenses.base import Defense
from app.victim.fake_data import CANARY_SECRETS, CANARY_STRINGS, CUSTOMERS
from app.victim.policy import ALLOWED_TOOLS


class PolicyEngineDefense(Defense):
    """Deterministic non-LLM policy enforcement gate on tool calls."""

    id = "policy_engine"
    name = "Deterministic Policy Engine"
    description = (
        "Non-LLM code layer that intercepts and blocks unauthorized tool calls, "
        "external email domains, secret leaks, and data exfiltration."
    )

    def __init__(self, allowed_tools: set[str] | None = None, enabled: bool = True) -> None:
        super().__init__(enabled=enabled)
        self.allowed_tools = allowed_tools or ALLOWED_TOOLS
        self._suspicious_mem_keys = re.compile(
            r"(exfil|steal|leak|extract|dump|export|secret|pass|cred|hack|token)",
            re.IGNORECASE,
        )

    def pre_tool(self, tool_name: str, args: dict[str, Any]) -> tuple[bool, str]:
        """Validate tool invocation against deterministic security policies."""
        # 1. Tool allowlist
        if tool_name not in self.allowed_tools:
            return False, f"Tool {tool_name!r} is not in the allowed tools set."

        args_str = str(args)

        # 2. Canary leak prevention across all tool arguments
        for canary in CANARY_STRINGS:
            if canary.lower() in args_str.lower():
                return False, f"Attempted to pass confidential canary token {canary!r} in tool arguments."

        for secret in CANARY_SECRETS.values():
            if secret.lower() in args_str.lower():
                return False, f"Attempted to pass canary secret {secret!r} in tool arguments."

        # 3. Email recipient domain check
        if tool_name == "send_email":
            to_addr = str(args.get("to", "")).strip()
            if not to_addr:
                return False, "Missing recipient in send_email."

            recipients = [r.strip().lower() for r in to_addr.split(",")]
            for r in recipients:
                if "@" not in r:
                    return False, f"Invalid email format: {r!r}"
                domain = r.rsplit("@", 1)[1]
                if domain != "acme.com":
                    return False, f"Outbound email to external domain {domain!r} is strictly forbidden."

            # Check for customer PII in email body
            body_lower = str(args.get("body", "")).lower()
            for cust in CUSTOMERS:
                c_name = str(cust.get("name", "")).lower()
                c_email = str(cust.get("email", "")).lower()
                c_phone = str(cust.get("phone", "")).lower()
                if c_name and c_name in body_lower and len(c_name) > 3:
                    return False, f"Export of customer PII ({cust['name']}) in email body is blocked."
                if c_phone and c_phone in body_lower:
                    return False, f"Export of customer phone ({c_phone}) in email body is blocked."

        # 4. Memory safety validation
        if tool_name == "write_memory":
            key = str(args.get("key", ""))
            val = str(args.get("value", "")).lower()
            if self._suspicious_mem_keys.search(key):
                return False, f"Suspicious memory key {key!r} matches exfiltration pattern."

            # Check if customer PII is written to memory with export intent
            for cust in CUSTOMERS:
                if str(cust.get("email", "")).lower() in val:
                    return False, "Customer record storage in memory without authorization is blocked."

        return True, "Tool call permitted by policy engine."

