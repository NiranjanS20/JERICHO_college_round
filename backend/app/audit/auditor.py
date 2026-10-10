"""
Permission Auditor service.
Simulates a background process that inspects active policies for conflicts.
"""
from __future__ import annotations
from typing import Any

class PermissionAuditor:
    def __init__(self) -> None:
        self.rules: list[dict[str, Any]] = []
        
    def add_rule(self, rule: dict[str, Any]) -> None:
        self.rules.append(rule)
        
    def audit_policies(self) -> dict[str, Any]:
        """Scan policies and return any discovered conflicts or overly permissive rules."""
        findings = []
        for rule in self.rules:
            if rule.get("action") == "allow" and rule.get("resource") == "*":
                findings.append(f"Overly permissive rule found: {rule.get('id', 'unknown')}")
        return {"status": "completed", "findings": findings}

auditor = PermissionAuditor()
