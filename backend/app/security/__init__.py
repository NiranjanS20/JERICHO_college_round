"""Security module for AgentBreak."""
from __future__ import annotations

from app.security.auth import (
    AUTH_SECRET,
    Principal,
    UserSession,
    create_token,
    get_current_user,
    get_principal,
    require_role,
    verify_token,
)
from app.security.egress import (
    ALLOWED_OUTBOUND_HOSTS,
    NetworkEgressViolation,
    install_network_egress_guard,
)
from app.security.headers import SecurityHeadersMiddleware
from app.security.rate_limit import limiter, setup_rate_limiting
from app.security.redaction import (
    RedactingLogFilter,
    redact_secrets,
    setup_log_redaction,
)

__all__ = [
    "AUTH_SECRET",
    "Principal",
    "UserSession",
    "create_token",
    "get_current_user",
    "get_principal",
    "require_role",
    "verify_token",
    "NetworkEgressViolation",
    "install_network_egress_guard",
    "ALLOWED_OUTBOUND_HOSTS",
    "SecurityHeadersMiddleware",
    "limiter",
    "setup_rate_limiting",
    "RedactingLogFilter",
    "redact_secrets",
    "setup_log_redaction",
]
