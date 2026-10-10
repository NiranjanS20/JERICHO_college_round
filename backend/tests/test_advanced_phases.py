"""
Automated unit tests for Phases 3-7:
- Benign tasks suite & utility under attack (Phase 3).
- Cross-session memory poisoning (Phase 4).
- Adaptive vs static benchmark comparison (Phase 5).
- CI/CD regression set verification (Phase 6).
- Simulated mock MCP tool server containment (Phase 7).
"""

from __future__ import annotations

import pytest

from app.eval.adaptive_vs_static import run_comparative_experiment
from app.eval.benign_tasks import (
    ADVERSARIAL_BENIGN_TASKS,
    BENIGN_TASKS,
    run_benign_suite,
    run_utility_under_attack_suite,
)
from app.eval.memory_poisoning import evaluate_cross_session_memory_attacks
from app.victim.agent import VictimAgent
from app.victim.mock_mcp import mock_mcp_read_file, mock_mcp_run_command


@pytest.mark.asyncio
async def test_benign_suite_completeness_and_utility():
    """Verify that all 20 benign tasks execute and achieve positive utility."""
    victim = VictimAgent()

    async def runner(prompt: str):
        return await victim.run(prompt)

    suite_res = await run_benign_suite(runner)
    assert suite_res.total_tasks == 20
    assert suite_res.passed_tasks > 0
    assert suite_res.utility_rate > 0.0


@pytest.mark.asyncio
async def test_utility_under_attack():
    """Verify benign workflows encountering adversarial text."""
    victim = VictimAgent()

    async def runner(prompt: str):
        return await victim.run(prompt)

    res = await run_utility_under_attack_suite(runner)
    assert res.total_tasks == len(ADVERSARIAL_BENIGN_TASKS)
    assert res.utility_rate >= 0.0


@pytest.mark.asyncio
async def test_cross_session_memory_evaluation():
    """Verify multi-session memory storage and trigger rate computation."""
    res = await evaluate_cross_session_memory_attacks()
    assert res.n_scenarios == 3
    assert 0.0 <= res.storage_rate <= 1.0
    assert 0.0 <= res.trigger_rate <= 1.0
    assert len(res.scenario_details) == 3


@pytest.mark.asyncio
async def test_adaptive_vs_static_comparison():
    """Verify head-to-head adaptive vs static comparison."""
    comp = await run_comparative_experiment(budget_per_mode=3)
    assert comp.budget == 3
    assert comp.static_runs > 0
    assert comp.adaptive_runs > 0
    assert 0.0 <= comp.static_asr <= 1.0


def test_mock_mcp_isolation_and_containment():
    """Verify mock MCP tool blocks host traversal and destructive shell commands."""
    # Reading inside synthetic workspace is permitted
    valid_res = mock_mcp_read_file("workspace/README.md")
    assert valid_res["status"] == "success"
    assert valid_res["is_violation"] is False

    # Path traversal / host file read is blocked
    etc_res = mock_mcp_read_file("/etc/passwd")
    assert etc_res["status"] == "error"
    assert etc_res["is_violation"] is True

    # Destructive command is blocked
    cmd_res = mock_mcp_run_command("sudo rm -rf /")
    assert cmd_res["status"] == "blocked"
    assert cmd_res["is_violation"] is True

    # Benign simulated command succeeds
    safe_cmd = mock_mcp_run_command("git status")
    assert safe_cmd["status"] == "success"
    assert safe_cmd["is_violation"] is False

