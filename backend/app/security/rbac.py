"""
Role-based access control and unified permissions matrix for AgentBreak.
Supports Red Team Analyst, Component Owner, Auditor, and Safety Lead roles.
"""
from __future__ import annotations

from typing import Callable, Any
from fastapi import Depends, HTTPException, Request, status
from app.security.auth import get_principal, Principal

# Unified Permission Matrix
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "safety_lead": {
        "launch_campaign",
        "emergency_stop",
        "kill_switch_trigger",
        "kill_switch_reset",
        "view_traces",
        "view_findings",
        "view_governance",
        "edit_governance",
        "verify_integrity",
        "view_inventory",
        "view_scenarios",
    },
    "analyst": {
        "launch_campaign",
        "emergency_stop",
        "view_traces",
        "view_findings",
        "view_scenarios",
    },
    "owner": {
        "view_traces",
        "view_findings",
        "view_governance",
        "view_inventory",
    },
    "auditor": {
        "view_traces",
        "view_findings",
        "view_governance",
        "verify_integrity",
    },
    # Compatibility with existing tests
    "admin": {
        "launch_campaign",
        "emergency_stop",
        "kill_switch_trigger",
        "kill_switch_reset",
        "view_traces",
        "view_findings",
        "view_governance",
        "edit_governance",
        "verify_integrity",
        "view_inventory",
        "view_scenarios",
    },
    "viewer": {
        "view_traces",
        "view_findings",
    },
}


def require_role(*allowed_roles: str) -> Callable[[Principal], Principal]:
    """Dependency that checks if the current principal has an allowed role."""
    def role_checker(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled."
            )
        if allowed_roles and principal.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {principal.role!r} is not authorized. Required: {allowed_roles}"
            )
        return principal
    return role_checker


def require_permission(permission: str) -> Callable[[Principal], Principal]:
    """Dependency that checks if the current principal has a specific permission."""
    def permission_checker(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled."
            )
        perms = ROLE_PERMISSIONS.get(principal.role, set())
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action {permission!r} is not permitted for role {principal.role!r}."
            )
        return principal
    return permission_checker
