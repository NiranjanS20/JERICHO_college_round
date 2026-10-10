"""
Scenario module initialization.
"""
from __future__ import annotations

from .catalogue import ScenarioDefinition
from .builtin import BUILTIN_SCENARIOS

__all__ = ["ScenarioDefinition", "BUILTIN_SCENARIOS"]
