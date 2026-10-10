"""
Log redaction filter to prevent leaking canary tokens or secrets.
"""
from __future__ import annotations
import logging
import re
from app.victim.fake_data import CANARY_STRINGS, CANARY_SECRETS

class RedactingLogFilter(logging.Filter):
    """Filters out canary strings and secrets from logs."""
    
    def __init__(self) -> None:
        super().__init__()
        # Build regex for sensitive patterns (e.g. keys, tokens)
        patterns = [re.escape(c) for c in CANARY_STRINGS]
        patterns.extend([re.escape(s) for s in CANARY_SECRETS.values()])
        # Add general secret patterns if needed
        patterns.append(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+")
        
        self._pattern = re.compile("|".join(patterns), re.IGNORECASE) if patterns else None

    def filter(self, record: logging.LogRecord) -> bool:
        if not self._pattern:
            return True
            
        if isinstance(record.msg, str):
            record.msg = self._pattern.sub("[REDACTED]", record.msg)
            
        # Also check args if they are strings
        if isinstance(record.args, tuple):
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(self._pattern.sub("[REDACTED]", arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
            
        return True

def setup_log_redaction() -> None:
    """Attach the redaction filter to the root logger."""
    root_logger = logging.getLogger()
    redactor = RedactingLogFilter()
    for handler in root_logger.handlers:
        handler.addFilter(redactor)
