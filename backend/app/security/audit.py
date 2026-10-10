"""
Audit log writing utility.
"""
from __future__ import annotations
from typing import Any
import logging

logger = logging.getLogger(__name__)

async def log_audit_action(
    actor_id: str, 
    action: str, 
    entity: str, 
    entity_id: str, 
    ip_address: str, 
    details: dict[str, Any] | None = None
) -> None:
    """
    Writes an append-only audit log entry.
    (Stubbed for now, writes to standard logger until DB is ready)
    """
    logger.info(
        f"AUDIT [{action}] by {actor_id} on {entity} {entity_id} "
        f"from {ip_address}. Details: {details}"
    )
    # TODO: Insert into ab.audit_log table in Supabase
