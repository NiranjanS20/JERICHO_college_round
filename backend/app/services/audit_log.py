"""
Audit logging service for AgentBreak.

Records security-critical events (logins, campaign launches, replays,
defense modifications, report exports) with request ID, actor, timestamp,
client IP, and status.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("agentbreak.audit")


@dataclass
class AuditEntry:
    """A tamper-evident audit record."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action: str = ""  # login | campaign.create | campaign.replay | defense.toggle | report.export
    actor_id: str = "anonymous"
    actor_role: str = "viewer"
    workspace_id: str = "default-workspace"
    client_ip: Optional[str] = None
    target_resource_id: Optional[str] = None
    status: str = "success"  # success | denied | error
    details: dict[str, Any] = field(default_factory=dict)


# In-memory circular buffer for fast local querying
_AUDIT_LOGS: list[AuditEntry] = []
_MAX_AUDIT_LOGS = 1000


def record_audit_event(
    action: str,
    actor_id: str,
    actor_role: str,
    workspace_id: str = "default-workspace",
    client_ip: Optional[str] = None,
    target_resource_id: Optional[str] = None,
    status: str = "success",
    details: Optional[dict[str, Any]] = None,
) -> AuditEntry:
    """Record an audit entry."""
    entry = AuditEntry(
        action=action,
        actor_id=actor_id,
        actor_role=actor_role,
        workspace_id=workspace_id,
        client_ip=client_ip,
        target_resource_id=target_resource_id,
        status=status,
        details=details or {},
    )
    _AUDIT_LOGS.append(entry)
    if len(_AUDIT_LOGS) > _MAX_AUDIT_LOGS:
        _AUDIT_LOGS.pop(0)

    logger.info("AUDIT EVENT: action=%s actor=%s status=%s resource=%s", action, actor_id, status, target_resource_id)
    return entry


def get_audit_logs(limit: int = 100, action_filter: Optional[str] = None) -> list[dict[str, Any]]:
    """Retrieve audit entries (newest first)."""
    logs = _AUDIT_LOGS
    if action_filter:
        logs = [e for e in logs if e.action == action_filter]
    return [asdict(e) for e in reversed(logs[-limit:])]

