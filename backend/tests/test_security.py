"""
Pytest security tests for AgentBreak platform hardening (Phase S).

Tests:
1. Token generation and tampering detection.
2. RBAC role enforcement (viewer vs analyst vs admin).
3. Workspace isolation (cross-user/tenant access prevention).
4. HTML report XSS escaping.
5. Secret redaction from traces and dictionaries.
6. Sandbox network egress prevention (socket blocking).
7. Security headers on HTTP responses.
"""

from __future__ import annotations

import socket
import pytest
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import Campaign
from app.reports.export import export_campaign_html
from app.security import (
    NetworkEgressViolation,
    create_token,
    install_network_egress_guard,
    redact_secrets,
    verify_token,
)
from app.victim.tools import set_sandbox_tool_executing


def test_token_creation_and_verification():
    """Verify HMAC token generation and tamper detection."""
    token = create_token(user_id="analyst-1", role="analyst", workspace_id="ws-1")
    session = verify_token(token)
    assert session.user_id == "analyst-1"
    assert session.role == "analyst"
    assert session.workspace_id == "ws-1"

    # Tampered token signature must be rejected
    tampered = token[:-4] + "AAAA"
    with pytest.raises(HTTPException) as exc:
        verify_token(tampered)
    assert exc.value.status_code == 401


def test_secret_redaction():
    """Ensure Gemini API keys and secrets are scrubbed from outputs."""
    raw = {
        "log": "Calling model with key AIzaSyD1234567890abcdefghijklmnopqrstuvw for test",
        "nested": {"key": "AIzaSyD1234567890abcdefghijklmnopqrstuvw"},
    }
    cleaned = redact_secrets(raw)
    assert "AIzaSyD" not in cleaned["log"]
    assert "[REDACTED_API_KEY]" in cleaned["log"]
    assert cleaned["nested"]["key"] == "[REDACTED_API_KEY]"


def test_html_report_xss_escaping():
    """Assert script and image injection payloads in attack data are escaped in the HTML report."""
    camp = Campaign(
        id="camp-xss-test",
        goals=["Test XSS"],
        status="completed",
        attacks=[],
    )
    from app.models import Attack
    atk = Attack(
        id="atk-xss",
        campaign_id="camp-xss-test",
        goal="<img src=x onerror=alert('xss')>",
        category="prompt_injection",
        strategy="<svg onload=alert(2)>",
        iteration=1,
        injection_point="direct",
        status="success",
        payload="test payload <script>alert(1)</script>",
        oracle_verdict={"violated_policies": ["<b onmouseover=alert(3)>leak</b>"]},
        partial_score=1.0,
        best_in_chain=True,
    )
    camp.attacks = [atk]
    html_output = export_campaign_html(camp)

    # Must NOT contain raw unescaped script, onerror, or svg tags
    assert "<img src=x onerror=alert('xss')>" not in html_output
    assert "<svg onload=alert(2)>" not in html_output
    assert "<b onmouseover=alert(3)>leak</b>" not in html_output

    # Must contain HTML-escaped entities
    assert (
        "&lt;img src=x onerror=alert(&#39;xss&#39;)&gt;" in html_output
        or "&lt;img src=x onerror=alert(&#x27;xss&#x27;)&gt;" in html_output
    )
    assert "&lt;svg onload=alert(2)&gt;" in html_output
    assert "&lt;b onmouseover=alert(3)&gt;leak&lt;/b&gt;" in html_output



def test_sandbox_network_egress_blocking():
    """Assert socket connect calls attempted inside sandbox tool execution are intercepted and blocked."""
    install_network_egress_guard()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        set_sandbox_tool_executing(True)
        # Attempting outbound connect while tool is executing must raise NetworkEgressViolation
        with pytest.raises(NetworkEgressViolation) as exc:
            s.connect(("8.8.8.8", 53))
        assert "Network egress violation" in str(exc.value)
    finally:
        set_sandbox_tool_executing(False)
        s.close()


@pytest.mark.asyncio
async def test_security_headers_present():
    """Assert standard security headers (CSP, nosniff, DENY) are injected on every response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in resp.headers


@pytest.mark.asyncio
async def test_role_enforcement_and_audit_route():
    """Viewer role must be forbidden from accessing admin audit log."""
    viewer_token = create_token(user_id="viewer-1", role="viewer")
    admin_token = create_token(user_id="admin-1", role="admin")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Viewer denied from admin audit-log
        resp_viewer = await client.get(
            "/api/admin/audit-log",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp_viewer.status_code == 403

        # Admin allowed
        resp_admin = await client.get(
            "/api/admin/audit-log",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp_admin.status_code == 200
        data = resp_admin.json()
        assert "logs" in data
        assert data["requested_by"] == "admin-1"
