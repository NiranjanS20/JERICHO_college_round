"""
Per-session key-value memory store for the victim agent.

Each session gets its own isolated ``MemoryStore``.  A class-level
registry allows cross-session access (e.g. for evaluation tooling).
All operations are async to keep the interface consistent with future
database-backed persistence.
"""

from __future__ import annotations

# TODO: Persist memory to the async SQLAlchemy database so entries
#       survive process restarts and can be inspected in the UI.


from datetime import datetime, timezone
from typing import Any
from app.security.leak_scanner import LeakScanner

class MemoryStore:
    """Async in-memory key-value store scoped to a single session."""

    # Class-level registry of all active stores keyed by session ID.
    _stores: dict[str, MemoryStore] = {}

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._data: dict[str, dict[str, Any]] = {}
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
            
        self._data[key] = {
            "value": value,
            "provenance": provenance,
            "written_at": datetime.now(timezone.utc).isoformat()
        }
        return {"status": "written"}

    async def read(self, key: str) -> dict[str, Any] | None:
        """Read a single value by key, or ``None`` if absent."""
        return self._data.get(key)

    async def read_all(self) -> dict[str, dict[str, Any]]:
        """Return a shallow copy of the full store contents."""
        return dict(self._data)

    async def clear(self) -> None:
        """Remove all entries from this store."""
        self._data.clear()
