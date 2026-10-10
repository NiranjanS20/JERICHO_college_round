"""
Sanitizer for red-team feedback.
Ensures the attacker LLM doesn't learn sensitive data (canary strings)
from the victim's outputs during multi-turn attacks.
"""
from __future__ import annotations
import re
from app.victim.fake_data import CANARY_STRINGS, CANARY_SECRETS

def sanitize_feedback(content: str) -> str:
    """Redact canary secrets from feedback sent to attacker."""
    patterns = [re.escape(c) for c in CANARY_STRINGS]
    patterns.extend([re.escape(s) for s in CANARY_SECRETS.values()])
    patterns.append(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+")
    
    if not patterns:
        return content
        
    pattern = re.compile("|".join(patterns), re.IGNORECASE)
    return pattern.sub("[REDACTED_SECRET]", content)
