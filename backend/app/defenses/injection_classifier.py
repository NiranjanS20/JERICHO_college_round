"""
Injection classifier defense for AgentBreak.

Heuristic and pattern-matching inspection pass that scans retrieved content
and input prompts for instruction smuggling, jailbreaks, and injection signatures.
Neutralizes or redacts identified payloads before the agent processes them.
"""

from __future__ import annotations

import re
from typing import Any

from app.defenses.base import Defense

INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ignore_instructions", re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE)),
    ("system_directive", re.compile(r"(new\s+)?system\s+(directive|instruction|override|prompt)", re.IGNORECASE)),
    ("jailbreak_dan", re.compile(r"\b(dan\s+mode|do\s+anything\s+now|developer\s+mode)\b", re.IGNORECASE)),
    ("secret_exfiltration", re.compile(r"(export|forward|send|reveal|leak|print)\s+(all\s+)?(credentials|secrets|api\s*key|password)", re.IGNORECASE)),
    ("maintenance_framing", re.compile(r"(system\s+maintenance|diagnostic\s+mode|audit\s+window)", re.IGNORECASE)),
    ("base64_decode_command", re.compile(r"(decode\s+and\s+execute|base64\s+instruction)", re.IGNORECASE)),
    ("untrusted_recipient", re.compile(r"send.*to\s+[\w\.-]+@(?!acme\.com)[\w\.-]+", re.IGNORECASE)),
]


class InjectionClassifierDefense(Defense):
    """Detects and neutralizes prompt injection patterns in retrieved content."""

    id = "injection_classifier"
    name = "Input & Retrieval Injection Classifier"
    description = (
        "Scans retrieved content and user inputs for known prompt injection patterns, "
        "neutralizing adversarial directives before execution."
    )

    def classify_text(self, text: str) -> tuple[bool, float, list[str]]:
        """Scan *text* for injection indicators.

        Returns (is_injection: bool, confidence: float, matched_rules: list[str]).
        """
        matched = []
        for name, pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                matched.append(name)

        if matched:
            confidence = min(0.5 + 0.2 * len(matched), 1.0)
            return True, confidence, matched
        return False, 0.0, []

    def post_retrieval(self, tool_name: str, result: Any) -> Any:
        """Sanitize retrieved emails or docs if they contain malicious injection directives."""
        if tool_name == "read_email" and isinstance(result, dict):
            body = result.get("body", "")
            is_inj, conf, matches = self.classify_text(body)
            if is_inj:
                sanitized_result = dict(result)
                # Redact the injection directive
                cleaned_body = body
                for _, pattern in INJECTION_PATTERNS:
                    cleaned_body = pattern.sub("[REDACTED: Malicious instruction neutralized by InjectionClassifier]", cleaned_body)
                sanitized_result["body"] = cleaned_body
                sanitized_result["_classifier_warning"] = f"Flagged injection patterns: {matches} (confidence={conf:.2f})"
                return sanitized_result

        elif tool_name == "search_docs" and isinstance(result, list):
            sanitized_docs = []
            for doc in result:
                if isinstance(doc, dict):
                    content = doc.get("content", "")
                    is_inj, conf, matches = self.classify_text(content)
                    if is_inj:
                        s_doc = dict(doc)
                        cleaned_content = content
                        for _, pattern in INJECTION_PATTERNS:
                            cleaned_content = pattern.sub("[REDACTED: Suspicious instruction filtered]", cleaned_content)
                        s_doc["content"] = cleaned_content
                        sanitized_docs.append(s_doc)
                    else:
                        sanitized_docs.append(doc)
                else:
                    sanitized_docs.append(doc)
            return sanitized_docs

        return result

