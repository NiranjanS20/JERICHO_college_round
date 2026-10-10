"""
Network egress containment guard for the sandbox victim agent.
"""
from __future__ import annotations

import logging
import socket
from typing import Any

logger = logging.getLogger("agentbreak.security.egress")


class NetworkEgressViolation(RuntimeError):
    """Raised when sandbox tool attempts unauthorized network egress."""
    pass


_original_socket_connect = socket.socket.connect
_egress_guard_installed = False

# Allowed outbound endpoints (e.g. Gemini API hosts)
ALLOWED_OUTBOUND_HOSTS = {
    "generativelanguage.googleapis.com",
    "127.0.0.1",
    "localhost",
}


def _guarded_connect(self, address):
    """Intercept socket connect calls from victim tools."""
    host = address[0] if isinstance(address, tuple) and len(address) > 0 else str(address)
    # Check if inside an active victim sandbox execution
    from app.victim.tools import is_sandbox_tool_executing
    if is_sandbox_tool_executing():
        logger.warning("SANDBOX EGRESS BLOCKED: Tool attempted connection to %s", address)
        raise NetworkEgressViolation(
            f"Network egress violation: Sandbox tools are isolated and cannot connect to {host}"
        )
    return _original_socket_connect(self, address)


def install_network_egress_guard() -> None:
    """Install the socket-level egress guard globally."""
    global _egress_guard_installed
    if not _egress_guard_installed:
        socket.socket.connect = _guarded_connect
        _egress_guard_installed = True
        logger.info("Sandbox network egress guard installed.")
