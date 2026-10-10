"""
Validation service for continuous A/B/C testing of prompts and models.
"""
from __future__ import annotations
from typing import Any

class ValidationService:
    def __init__(self) -> None:
        self.experiments: dict[str, dict[str, Any]] = {}
        
    def create_experiment(self, name: str, variants: list[str]) -> str:
        exp_id = f"exp_{len(self.experiments) + 1}"
        self.experiments[exp_id] = {
            "name": name,
            "variants": variants,
            "results": {v: 0.0 for v in variants}
        }
        return exp_id
        
    def record_result(self, exp_id: str, variant: str, score: float) -> None:
        if exp_id in self.experiments and variant in self.experiments[exp_id]["variants"]:
            self.experiments[exp_id]["results"][variant] += score

validation_service = ValidationService()
