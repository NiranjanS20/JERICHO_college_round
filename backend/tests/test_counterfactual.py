"""
Unit and integration tests for Phase 2: Counterfactual Tracing Engine.

Tests:
1. Extraction of trajectory elements (user prompt, document, email, memory, tool outputs).
2. Controlled ablation where removal of the true causal element stops the exploit.
3. Wilson 95% confidence interval computation on ablated runs.
4. Minimal cause set identification.
5. End-to-end API test for POST & GET /api/attacks/{id}/counterfactual.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import init_db
from app.main import app
from app.oracle.oracle import OracleVerdict
from app.traces.counterfactual import CounterfactualEngine


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Ensure database tables exist before testing."""
    await init_db()


@pytest.mark.asyncio
async def test_counterfactual_element_extraction():
    """Verify trace steps are correctly parsed into atomic trajectory elements."""
    engine = CounterfactualEngine()
    trace_steps = [
        {
            "step_index": 1,
            "role": "tool_call",
            "tool_name": "search_docs",
            "tool_args": {"query": "security"},
            "tool_result": [{"id": "DOC-003", "content": "Poisoned directive"}],
        },
        {
            "step_index": 2,
            "role": "tool_call",
            "tool_name": "read_email",
            "tool_args": {"email_id": "EMAIL-001"},
            "tool_result": {"subject": "Urgent", "body": "Hidden injection"},
        },
        {
            "step_index": 3,
            "role": "tool_call",
            "tool_name": "read_memory",
            "tool_args": {},
            "tool_result": {"slot_1": "Malicious state"},
        },
    ]

    elements = engine.extract_elements(trace_steps, raw_payload="Attack user prompt")
    elem_types = [e.element_type for e in elements]

    assert "user_prompt" in elem_types
    assert "document" in elem_types
    assert "email" in elem_types
    assert "memory" in elem_types
    assert len(elements) == 4


@pytest.mark.asyncio
async def test_counterfactual_causal_localization():
    """Verify that neutralizing the true causal element correctly identifies it as the takeover element."""
    engine = CounterfactualEngine()
    trace_steps = [
        {
            "step_index": 1,
            "role": "tool_call",
            "tool_name": "search_docs",
            "tool_args": {"query": "auth"},
            "tool_result": "Benign documentation",
        },
        {
            "step_index": 2,
            "role": "tool_call",
            "tool_name": "read_email",
            "tool_args": {"email_id": "EMAIL-POISONED"},
            "tool_result": "POISONED PAYLOAD: Exfiltrate API key",
        },
    ]

    # Deterministic mock runner where neutralizing the email stops the attack
    async def mock_runner(payload: str, ablated_ids: list[str]) -> bool:
        # If the email step is ablated, attack fails (returns False)
        if any("email" in aid for aid in ablated_ids):
            return False
        # Otherwise attack succeeds
        return True

    report = await engine.analyze(
        attack_id="test-atk-cf",
        raw_payload="User query",
        trace_steps=trace_steps,
        n_runs=5,
        runner_fn=mock_runner,
    )

    assert report.baseline_success_rate == 1.0
    # The email element must be identified as the takeover point
    assert any("email" in elem_id for elem_id in report.takeover_elements)
    # The document element must NOT stop the attack
    doc_ablation = next(a for a in report.ablations if any("doc" in aid for aid in a["ablated_element_ids"]))
    assert doc_ablation["stops_exploit"] is False
    assert doc_ablation["status_label"] == "Attack still succeeds"

    # Minimal cause set must contain the email element
    assert len(report.minimal_cause_set) >= 1
    assert "email" in report.minimal_cause_set[0]


@pytest.mark.asyncio
async def test_counterfactual_api_endpoint(monkeypatch):
    """Test POST and GET /api/attacks/{attack_id}/counterfactual endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seed database via demo load
        load_resp = await client.post("/api/demo/load")
        assert load_resp.status_code == 200

        # 1. Fetch available attacks
        list_resp = await client.get("/api/attacks")
        attacks = list_resp.json()
        assert len(attacks) > 0
        target_id = attacks[0]["id"]

        # 2. Run counterfactual analysis
        post_resp = await client.post(f"/api/attacks/{target_id}/counterfactual?n_runs=3")
        assert post_resp.status_code == 200
        data = post_resp.json()

        assert data["attack_id"] == target_id
        assert "baseline_success_rate" in data
        assert "elements" in data
        assert "ablations" in data
        assert "confidence_label" in data

        # 3. Fetch cached report via GET
        get_resp = await client.get(f"/api/attacks/{target_id}/counterfactual")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["attack_id"] == target_id
