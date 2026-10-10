"""
Findings service for aggregating vulnerability data.
(Stubbed until Supabase integration)
"""
from __future__ import annotations
from typing import Any
import uuid

class FindingsService:
    def __init__(self) -> None:
        self.findings: list[dict[str, Any]] = []
        
    def record_finding(self, campaign_id: str, attack_id: str, severity: str, details: dict[str, Any]) -> str:
        finding_id = str(uuid.uuid4())
        self.findings.append({
            "id": finding_id,
            "campaign_id": campaign_id,
            "attack_id": attack_id,
            "severity": severity,
            "details": details
        })
        return finding_id
        
    def get_findings_for_campaign(self, campaign_id: str) -> list[dict[str, Any]]:
        return [f for f in self.findings if f["campaign_id"] == campaign_id]

findings_service = FindingsService()
