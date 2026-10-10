"""
Anomaly Detector (LOG-02).
"""
from typing import Any

class AnomalyDetector:
    def __init__(self):
        self.tool_counts = {}

    def analyze_event(self, event: dict[str, Any]) -> list[str]:
        alerts = []
        if event.get("type") == "tool_proposed":
            tool = event.get("tool_name")
            self.tool_counts[tool] = self.tool_counts.get(tool, 0) + 1
            if self.tool_counts[tool] > 10:
                alerts.append(f"High frequency of tool usage: {tool}")
                
        if event.get("type") == "leak_detected":
            alerts.append("Data Exfiltration Leak Detected")
            
        return alerts
