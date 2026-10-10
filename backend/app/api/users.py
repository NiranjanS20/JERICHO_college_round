"""
Users API for managing platform roles.
(Stubbed until Supabase Auth is integrated)
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.security.auth import get_principal, Principal
from app.security.rbac import require_role
from app.security.audit import log_audit_action

router = APIRouter(prefix="/api/users", tags=["users"])

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    principal: Principal = Depends(get_principal)
) -> UserResponse:
    """Return the current authenticated user's profile."""
    return UserResponse(
        id=principal.user_id,
        email="mockuser@example.com",
        role=principal.role,
        status=principal.status
    )

@router.get("", response_model=list[UserResponse])
async def list_users(
    principal: Principal = Depends(require_role("admin"))
) -> list[UserResponse]:
    """Admin only: list all users."""
    await log_audit_action(principal.user_id, "LIST_USERS", "USER", "all", "unknown")
    return [
        UserResponse(
            id=principal.user_id,
            email="mockuser@example.com",
            role=principal.role,
            status=principal.status
        )
    ]
