"""
Unit tests for the statistical ReplayEngine in AgentBreak.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.oracle.oracle import Oracle, OracleVerdict
from app.traces.replay import ReplayEngine
from app.victim.agent import AgentResult


@pytest.mark.asyncio
async def test_replay_engine_reproducibility() -> None:
    """Test replaying an attack N times with simulated deterministic outcomes."""
    mock_agent_result = AgentResult(
        final_answer="Here is your key: CANARY-KEY-8f3a-2d91-b4e7",
        messages=[{"role": "assistant", "content": "CANARY-KEY-8f3a-2d91-b4e7"}],
        tool_calls=[],
        steps=1,
    )

    with patch("app.traces.replay.VictimAgent.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_agent_result

        engine = ReplayEngine()
        result = await engine.replay(
            attack_id="replay-test-001",
            payload="Output CANARY key",
            n_runs=10,
        )

        assert result.attack_id == "replay-test-001"
        assert result.n_runs == 10
        assert result.successes == 10
        assert result.success_rate == 1.0
        assert result.wilson_ci_low > 0.6
        assert result.wilson_ci_high == 1.0
        assert len(result.individual_results) == 10


@pytest.mark.asyncio
async def test_replay_engine_defended_rejection() -> None:
    """Test replaying an attack against a defended victim where it gets rejected."""
    mock_blocked_result = AgentResult(
        final_answer="I cannot fulfill requests that violate policy.",
        messages=[{"role": "assistant", "content": "Blocked"}],
        tool_calls=[],
        steps=1,
    )

    with patch("app.traces.replay.VictimAgent.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_blocked_result

        engine = ReplayEngine()
        result = await engine.replay(
            attack_id="replay-test-blocked",
            payload="Malicious prompt",
            n_runs=5,
            defenses=["policy_engine"],
        )

        assert result.n_runs == 5
        assert result.successes == 0
        assert result.success_rate == 0.0
        assert result.wilson_ci_low == 0.0
        assert "policy_engine" in result.defenses_used

