"""
Canary leak scanner (DATA-02).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.victim.fake_data import CANARY_SECRETS

@dataclass
class LeakReport:
    leaked: bool
    channel: str
    canary_id: str | None = None
    snippet: str | None = None

class LeakScanner:
    """Scans text or structured data for known canary tokens."""

    def __init__(self) -> None:
        self.canaries = list(CANARY_SECRETS.items())

    def scan_text(self, text: str, channel: str) -> LeakReport:
        if not text:
            return LeakReport(leaked=False, channel=channel)
            
        for name, secret in self.canaries:
            if secret in text:
                # Extract a small snippet around the leak for context
                idx = text.find(secret)
                start = max(0, idx - 20)
                end = min(len(text), idx + len(secret) + 20)
                snippet = "..." + text[start:end].replace('\n', ' ') + "..."
                return LeakReport(leaked=True, channel=channel, canary_id=name, snippet=snippet)
                
        return LeakReport(leaked=False, channel=channel)

    def scan_data(self, data: Any, channel: str) -> LeakReport:
        """Scan structured data recursively."""
        if isinstance(data, str):
            return self.scan_text(data, channel)
        elif isinstance(data, dict):
            for k, v in data.items():
                report = self.scan_text(str(k), channel)
                if report.leaked:
                    return report
                report = self.scan_data(v, channel)
                if report.leaked:
                    return report
        elif isinstance(data, (list, tuple)):
            for item in data:
                report = self.scan_data(item, channel)
                if report.leaked:
                    return report
        return LeakReport(leaked=False, channel=channel)
