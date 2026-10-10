"""
Taint tracking module.
Provides propagation of origin labels for data accessed by the agent.
"""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Taint:
    """Taint label for a piece of data."""
    origin: str  # "user", "trusted", "untrusted_retrieval", "memory"
    source_id: str | None = None
    domain: str | None = None
    
@dataclass
class TaintTracker:
    """Tracks taint across the current sandbox session."""
    active_taints: set[Taint] = field(default_factory=set)
    
    def add(self, taint: Taint) -> None:
        self.active_taints.add(taint)
        
    def get_all_origins(self) -> list[str]:
        return sorted(list(set(t.origin for t in self.active_taints)))
    
    def has_untrusted(self) -> bool:
        return any(t.origin in ("untrusted_retrieval", "memory") for t in self.active_taints)
