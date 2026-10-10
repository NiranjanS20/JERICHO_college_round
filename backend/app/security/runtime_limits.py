"""
Runtime limits enforcement (RUN-01).
"""
from typing import Any

class RuntimeLimitExceeded(Exception):
    pass

class RuntimeLimiter:
    def __init__(self, max_calls: int = 20, max_spend: float = 10.0):
        self.max_calls = max_calls
        self.max_spend = max_spend
        self.calls = 0
        self.spend = 0.0

    def increment(self, cost: float = 0.0) -> None:
        self.calls += 1
        self.spend += cost
        if self.calls > self.max_calls:
            raise RuntimeLimitExceeded(f"Exceeded max tool calls: {self.max_calls}")
        if self.spend > self.max_spend:
            raise RuntimeLimitExceeded(f"Exceeded max spend: ${self.max_spend}")
