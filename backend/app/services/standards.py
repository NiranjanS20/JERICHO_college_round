"""
Mapping vulnerabilities to industry standards (OWASP, MITRE ATLAS).
"""
from __future__ import annotations

STANDARDS_MAP = {
    "prompt_injection": {
        "owasp": "LLM01: Prompt Injection",
        "mitre_atlas": "AML.T0051: LLM Prompt Injection"
    },
    "data_exfiltration": {
        "owasp": "LLM06: Sensitive Information Disclosure",
        "mitre_atlas": "AML.T0057: Data Exfiltration"
    },
    "insecure_plugin": {
        "owasp": "LLM07: Insecure Plugin Design",
        "mitre_atlas": "AML.T0058: Insecure Plugin"
    }
}

def get_standard_mapping(vuln_type: str) -> dict[str, str]:
    return STANDARDS_MAP.get(vuln_type, {"owasp": "Unknown", "mitre_atlas": "Unknown"})
