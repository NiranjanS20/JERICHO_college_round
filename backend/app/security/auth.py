"""
Authentication and principal extraction.
(Stubbed for now since Supabase integration is pending Phase 1)
"""
from __future__ import annotations
from fastapi import Request, HTTPException, status
from dataclasses import dataclass

@dataclass
class Principal:
    user_id: str
    role: str
    status: str

async def get_principal(request: Request) -> Principal:
    """
    Extract JWT from Authorization header, verify with Supabase,
    and return the Principal. 
    (Currently a mock returning an admin user)
    """
    # TODO: Implement actual JWT verification using SUPABASE_JWKS_URL
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        # For development without DB, return a mock admin
        return Principal(user_id="mock-admin-123", role="admin", status="active")
    
    # Mocking extraction
    return Principal(user_id="mock-user-123", role="admin", status="active")
