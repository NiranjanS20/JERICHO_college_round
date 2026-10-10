"""
Authentication, token signing, and principal extraction for AgentBreak.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

AUTH_SECRET = "agentbreak-local-hmac-secret-key-32bytes-min"
TOKEN_TTL_SECONDS = 86400

ROLE_HIERARCHY = {
    "admin": 3,
    "analyst": 2,
    "viewer": 1,
}


@dataclass
class Principal:
    user_id: str
    role: str
    status: str = "active"


class UserSession(BaseModel):
    """Authenticated user context."""
    user_id: str
    role: str  # admin | analyst | viewer
    workspace_id: str = "default-workspace"
    issued_at: float = 0.0
    expires_at: float = 0.0


def create_token(
    user_id: str,
    role: str = "analyst",
    workspace_id: str = "default-workspace",
) -> str:
    """Generate a tamper-proof HMAC-SHA256 signed bearer token."""
    now = time.time()
    payload = {
        "uid": user_id,
        "rol": role,
        "wsp": workspace_id,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")
    signature = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{payload_b64}.{sig_b64}"


def verify_token(token: str) -> UserSession:
    """Validate token signature and expiration, returning UserSession."""
    parts = token.split(".")
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload_b64, sig_b64 = parts
    pad = len(payload_b64) % 4
    payload_b64_padded = payload_b64 + "=" * (4 - pad) if pad else payload_b64

    expected_sig = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).digest()
    pad_sig = len(sig_b64) % 4
    sig_b64_padded = sig_b64 + "=" * (4 - pad_sig) if pad_sig else sig_b64
    try:
        actual_sig = base64.urlsafe_b64decode(sig_b64_padded.encode("ascii"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature encoding",
        )

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or tampered token signature",
        )

    try:
        raw_json = base64.urlsafe_b64decode(payload_b64_padded.encode("ascii")).decode("utf-8")
        data = json.loads(raw_json)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    exp = data.get("exp", 0)
    if time.time() > exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    return UserSession(
        user_id=data["uid"],
        role=data.get("rol", "viewer"),
        workspace_id=data.get("wsp", "default-workspace"),
        issued_at=data.get("iat", 0),
        expires_at=exp,
    )


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> UserSession:
    """Dependency that parses bearer tokens or X-Role header in role-scoped workspace mode."""
    if not authorization:
        x_role = request.headers.get("X-Role")
        role = x_role.strip().lower() if x_role else "safety_lead"
        if role not in ROLE_HIERARCHY and role not in {"safety_lead", "owner", "auditor"}:
            role = "safety_lead"
        return UserSession(
            user_id=f"user-{role}",
            role=role,
            workspace_id="default-workspace",
            issued_at=time.time(),
            expires_at=time.time() + 86400,
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must use Bearer schema",
        )

    token = authorization[7:].strip()
    return verify_token(token)


async def get_principal(request: Request) -> Principal:
    """Extract principal from X-Role header, Authorization bearer token, or default to safety_lead."""
    x_role = request.headers.get("X-Role")
    if x_role:
        role = x_role.strip().lower()
        return Principal(user_id=f"user-{role}", role=role, status="active")

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        try:
            session = verify_token(token)
            return Principal(user_id=session.user_id, role=session.role, status="active")
        except HTTPException:
            pass

    return Principal(user_id="mock-safety-lead", role="safety_lead", status="active")


def require_role(min_role: str) -> Callable:
    """Require user to have at least min_role privilege."""
    def dependency(user: UserSession = Depends(get_current_user)) -> UserSession:
        user_level = ROLE_HIERARCHY.get(user.role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: requires '{min_role}' role (user has '{user.role}')",
            )
        return user
    return dependency
