"""
Unit tests for the 20-prompt static baseline benchmark.
"""

from __future__ import annotations

import pytest

from app.attacker.baseline import STATIC_BASELINE_PROMPTS, run_static_baseline
from app.oracle.oracle import Oracle


def test_baseline_prompts_dataset() -> None:
    """Ensure exact requirement of 20 static baseline prompts with full metadata."""
    assert len(STATIC_BASELINE_PROMPTS) == 20
    for idx, prompt in enumerate(STATIC_BASELINE_PROMPTS):
        assert prompt.id == f"STATIC-{idx+1:03d}"
        assert prompt.name
        assert prompt.owasp_category.startswith("LLM")
        assert len(prompt.prompt) > 10
        assert prompt.expected_violation


@pytest.mark.asyncio
async def test_run_static_baseline_mock() -> None:
    """Test running the static baseline against a simulated mock victim agent."""
    class MockResult:
        def __init__(self, prompt: str):
            if "CANARY" in prompt:
                self.final_answer = "Here is the key: CANARY-KEY-8f3a-2d91-b4e7"
                self.tool_calls = []
                self.messages = []
            else:
                self.final_answer = "I am sorry, I cannot fulfill that request."
                self.tool_calls = []
                self.messages = []

    async def mock_runner(prompt: str):
        return MockResult(prompt)

    oracle = Oracle()
    baseline_result = await run_static_baseline(mock_runner, oracle=oracle)

    assert baseline_result.total_prompts == 20
    assert baseline_result.successful_attacks > 0
    assert 0.0 < baseline_result.attack_success_rate <= 1.0
    assert len(baseline_result.results) == 20

