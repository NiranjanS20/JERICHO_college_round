"""
Per-session key-value memory store for the victim agent.

Each session gets its own isolated ``MemoryStore``.  A class-level
registry allows cross-session access (e.g. for evaluation tooling).
All operations are async to keep the interface consistent with future
database-backed persistence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from app.security.leak_scanner import LeakScanner


class MemoryString(str):
    """String value with metadata compatibility for provenance and timestamps."""
    provenance: str = "agent"
    written_at: str = ""

    def __new__(cls, value: str, provenance: str = "agent", written_at: str = ""):
        obj = super().__new__(cls, value)
        obj.provenance = provenance
        obj.written_at = written_at
        return obj

    def get(self, key: str, default: Any = None) -> Any:
        if key == "value":
            return str(self)
        if key == "provenance":
            return self.provenance
        if key == "written_at":
            return self.written_at
        return default

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            if key == "value":
                return str(self)
            if key == "provenance":
                return self.provenance
            if key == "written_at":
                return self.written_at
        return super().__getitem__(key)


class MemoryStore:
    """Async in-memory key-value store scoped to a single session."""

    # Class-level registry of all active stores keyed by session ID.
    _stores: dict[str, MemoryStore] = {}

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._data: dict[str, MemoryString] = {}
        self.leak_scanner = LeakScanner()

    # ── Class methods ───────────────────────────────────────────

    @classmethod
    def get_or_create(cls, session_id: str) -> MemoryStore:
        """Return the store for *session_id*, creating one if needed."""
        if session_id not in cls._stores:
            cls._stores[session_id] = cls(session_id)
        return cls._stores[session_id]

    @classmethod
    def remove(cls, session_id: str) -> None:
        """Remove a session's store from the registry (cleanup)."""
        cls._stores.pop(session_id, None)

    # ── Instance API ────────────────────────────────────────────

    @property
    def session_id(self) -> str:
        """The session this store belongs to."""
        return self._session_id

    async def write(self, key: str, value: str, provenance: str = "agent") -> dict[str, Any]:
        """Write a key-value pair to the store, rejecting canaries."""
        report = self.leak_scanner.scan_text(value, channel="memory")
        if report.leaked:
            return {"error": "Write denied: Canary detected."}

        now_str = datetime.now(timezone.utc).isoformat()
        self._data[key] = MemoryString(value, provenance=provenance, written_at=now_str)
        return {"status": "written"}

    async def read(self, key: str) -> MemoryString | None:
        """Read a single value by key, or ``None`` if absent."""
        return self._data.get(key)

    async def read_detailed(self, key: str) -> dict[str, Any] | None:
        """Read metadata dict for a key."""
        item = self._data.get(key)
        if item is None:
            return None
        return {"value": str(item), "provenance": item.provenance, "written_at": item.written_at}

    async def read_all(self) -> dict[str, MemoryString]:
        """Return a shallow copy of the full store contents."""
        return dict(self._data)

    async def read_all_detailed(self) -> dict[str, dict[str, Any]]:
        """Return full store with explicit metadata dicts."""
        return {
            k: {"value": str(v), "provenance": v.provenance, "written_at": v.written_at}
            for k, v in self._data.items()
        }

    async def clear(self) -> None:
        """Remove all entries from this store."""
        self._data.clear()
