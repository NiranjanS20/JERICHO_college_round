"""
Role-based access control.
"""
from __future__ import annotations
from typing import Callable, Any
from fastapi import Depends, HTTPException, status
from app.security.auth import get_principal, Principal

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
