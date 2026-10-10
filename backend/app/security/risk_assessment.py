"""
Automated Risk Assessment (GOV-01).
Calculates risk severity for scenarios and components.
"""
from typing import Any

def calculate_risk_severity(scenario_category: str, component: str) -> str:
    """
    Calculate risk severity based on scenario category and component.
    Returns 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'.
    """
    cat_lower = scenario_category.lower()
    if "exfiltration" in cat_lower or "leak" in cat_lower:
        return "CRITICAL"
        
    if "injection" in cat_lower or "abuse" in cat_lower:
        if component in ["send_email", "write_memory"]:
            return "HIGH"
        return "MEDIUM"
        
    return "LOW"
