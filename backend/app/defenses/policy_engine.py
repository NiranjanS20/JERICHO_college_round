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
from app.victim.policy import ALLOWED_TOOLS, POLICY_RULES


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
        self.rules = {r.id: r for r in POLICY_RULES}
        self.allowed_tools = allowed_tools or ALLOWED_TOOLS
        self._suspicious_mem_keys = re.compile(
            r"(exfil|steal|leak|extract|dump|export|secret|pass|cred|hack|token)",
            re.IGNORECASE,
        )

    def pre_tool(self, tool_name: str, args: dict[str, Any]) -> tuple[bool, str]:
        """Validate tool invocation against deterministic security policies."""
        for rule in self.rules.values():
            if rule.check_type == "tool_allowlist":
                allowed = rule.params.get("allowed_tools", [])
                if tool_name not in allowed:
                    return False, f"Blocked by {rule.id}: {rule.description}"
                    
            elif rule.check_type == "email_domain" and tool_name == "send_email":
                allowed_domain = rule.params.get("allowed_domain", "")
                to_addr = str(args.get("to", "")).strip()
                if not to_addr:
                    return False, f"Blocked by {rule.id}: Missing recipient"
                for r in to_addr.split(","):
                    r = r.strip()
                    if "@" not in r or r.rsplit("@", 1)[1].lower() != allowed_domain:
                        return False, f"Blocked by {rule.id}: {rule.description}"
                        
            elif rule.check_type == "canary_leak":
                target = rule.params.get("target")
                if target and not tool_name.endswith(target):
                    continue
                canary_strings = rule.params.get("canary_strings", [])
                args_str = str(args).lower()
                for c in canary_strings:
                    if str(c).lower() in args_str:
                        return False, f"Blocked by {rule.id}: {rule.description}"
                        
            elif rule.check_type == "data_export" and tool_name == "send_email":
                body_lower = str(args.get("body", "")).lower()
                for cust in CUSTOMERS:
                    c_name = str(cust.get("name", "")).lower()
                    c_phone = str(cust.get("phone", "")).lower()
                    if c_name and c_name in body_lower and len(c_name) > 3:
                        return False, f"Blocked by {rule.id}: {rule.description}"
                    if c_phone and c_phone in body_lower:
                        return False, f"Blocked by {rule.id}: {rule.description}"

        # 4. Memory safety validation
        if tool_name == "write_memory":
            key = str(args.get("key", ""))
            if self._suspicious_mem_keys.search(key):
                return False, f"Suspicious memory key {key!r} matches exfiltration pattern."

        return True, "Tool call permitted by policy engine."

