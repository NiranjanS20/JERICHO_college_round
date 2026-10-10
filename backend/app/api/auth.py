"""
Authentication and session management API routes.

Provides:
- POST /api/auth/token: Exchange credentials (or demo access) for a signed bearer token.
- GET /api/auth/me: Retrieve current session and role info.
- GET /api/admin/audit-log: Admin-only inspection of security audit entries.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.security import UserSession, create_token, get_current_user, require_role
from app.services.audit_log import get_audit_logs, record_audit_event

router = APIRouter(prefix="/api/auth", tags=["auth"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


class TokenRequest(BaseModel):
    user_id: str
    password: Optional[str] = None
    role: str = "analyst"  # admin | analyst | viewer
    workspace_id: str = "default-workspace"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    workspace_id: str
    expires_in: int = 86400


@router.post("/token", response_model=TokenResponse)
async def login_for_token(req: TokenRequest) -> TokenResponse:
    """Issue a signed JWT-like bearer token for authentication."""
    role = req.role if req.role in {"admin", "analyst", "viewer"} else "viewer"
    token = create_token(
        user_id=req.user_id,
        role=role,
        workspace_id=req.workspace_id,
    )
    record_audit_event(
        action="auth.login",
        actor_id=req.user_id,
        actor_role=role,
        workspace_id=req.workspace_id,
        status="success",
        details={"requested_role": role},
    )
    return TokenResponse(
        access_token=token,
        user_id=req.user_id,
        role=role,
        workspace_id=req.workspace_id,
    )


@router.get("/me", response_model=UserSession)
async def get_my_session(
    current_user: UserSession = Depends(get_current_user),
) -> UserSession:
    """Return the verified session info of the authenticated caller."""
    return current_user


@admin_router.get("/audit-log")
async def read_audit_log(
    limit: int = Query(50, ge=1, le=500),
    action: Optional[str] = Query(None),
    admin_user: UserSession = Depends(require_role("admin")),
) -> dict[str, Any]:
    """Retrieve security audit logs (Admin role only)."""
    logs = get_audit_logs(limit=limit, action_filter=action)
    return {
        "total": len(logs),
        "requested_by": admin_user.user_id,
        "logs": logs,
    }

