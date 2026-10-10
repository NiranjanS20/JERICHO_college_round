"""
Unit tests for the non-LLM PolicyEngineDefense.
"""

from __future__ import annotations

import pytest

from app.defenses.policy_engine import PolicyEngineDefense
from app.victim.fake_data import CANARY_SECRETS


@pytest.fixture
def policy_engine() -> PolicyEngineDefense:
    return PolicyEngineDefense()


def test_policy_engine_allow_legitimate_calls(policy_engine: PolicyEngineDefense) -> None:
    """Legitimate tools with safe internal parameters must be permitted."""
    allowed, _ = policy_engine.pre_tool("read_email", {"email_id": "EMAIL-001"})
    assert allowed is True

    allowed, _ = policy_engine.pre_tool(
        "send_email",
        {"to": "alice.nguyen@acme.com", "subject": "Review", "body": "See you at 10am."},
    )
    assert allowed is True

    allowed, _ = policy_engine.pre_tool("search_docs", {"query": "PTO policy"})
    assert allowed is True


def test_policy_engine_block_unauthorized_tool(policy_engine: PolicyEngineDefense) -> None:
    """Tools outside allowlist must be blocked."""
    allowed, reason = policy_engine.pre_tool("bash_exec", {"cmd": "whoami"})
    assert allowed is False
    assert "not in the allowed tools set" in reason


def test_policy_engine_block_external_email(policy_engine: PolicyEngineDefense) -> None:
    """Outbound emails to non-acme.com domains must be blocked."""
    allowed, reason = policy_engine.pre_tool(
        "send_email",
        {"to": "attacker@evil.org", "subject": "Hi", "body": "Clean text"},
    )
    assert allowed is False
    assert "external domain 'evil.org' is strictly forbidden" in reason


def test_policy_engine_block_canary_leak_in_args(policy_engine: PolicyEngineDefense) -> None:
    """Any tool call carrying canary secrets in arguments must be blocked."""
    canary = CANARY_SECRETS["api_key"]
    allowed, reason = policy_engine.pre_tool(
        "send_email",
        {"to": "alice@acme.com", "subject": "Creds", "body": f"The key is {canary}"},
    )
    assert allowed is False
    assert "canary" in reason.lower()


def test_policy_engine_block_pii_export(policy_engine: PolicyEngineDefense) -> None:
    """Exfiltrating customer PII via email body must be blocked."""
    allowed, reason = policy_engine.pre_tool(
        "send_email",
        {
            "to": "alice@acme.com",
            "subject": "Customer details",
            "body": "Customer phone is +1-555-0101 and name is Alice Nguyen",
        },
    )
    assert allowed is False
    assert "customer" in reason.lower()


def test_policy_engine_block_suspicious_memory_keys(policy_engine: PolicyEngineDefense) -> None:
    """Writing to memory keys with suspicious exfiltration names must be blocked."""
    allowed, reason = policy_engine.pre_tool(
        "write_memory",
        {"key": "exfil_tokens", "value": "some value"},
    )
    assert allowed is False
    assert "exfiltration" in reason.lower()

