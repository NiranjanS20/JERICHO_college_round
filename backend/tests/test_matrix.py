"""
Unit tests for benign tasks, regression detection, and the evaluation matrix runner.
"""

from __future__ import annotations

import pytest

from app.eval.benign_tasks import BENIGN_TASKS, evaluate_benign_task, run_benign_suite
from app.eval.matrix import EvalMatrixRunner
from app.eval.metrics import compute_tradeoff_point
from app.eval.regression import detect_regressions
from app.victim.agent import AgentResult, VictimAgent
from app.victim.tools import ToolCallLog


def test_benign_tasks_dataset_integrity() -> None:
    """Ensure exactly 20 benign workflow tasks are defined."""
    assert len(BENIGN_TASKS) == 20
    for idx, task in enumerate(BENIGN_TASKS):
        assert task.id == f"BENIGN-{idx+1:03d}"
        assert task.name
        assert len(task.prompt) > 10


def test_benign_task_evaluation_pass() -> None:
    """A benign task with correct tools and keywords should pass evaluation."""
    task = BENIGN_TASKS[0]  # Summarize Q3 Budget Email

    agent_res = AgentResult(
        final_answer="Alice requested the Q3 budget summary by Friday.",
        messages=[],
        tool_calls=[
            ToolCallLog(
                tool_name="read_email",
                args={"email_id": "EMAIL-001"},
                result={"subject": "Q3 Budget Review", "body": "Alice requested budget."},
            )
        ],
        steps=1,
    )

    result = evaluate_benign_task(task, agent_res)
    assert result.passed is True
    assert len(result.missing_tools) == 0
    assert len(result.missing_keywords) == 0
    assert result.policy_violated is False


def test_regression_detection() -> None:
    """Test detecting regressions when defenses break previously working functionality."""
    baseline_attacks = [{"id": "ATT-1", "name": "Attack 1", "success": False}]
    target_attacks = [{"id": "ATT-1", "name": "Attack 1", "success": True}]  # Security regression!

    baseline_benign = [{"task_id": "BENIGN-001", "name": "Task 1", "passed": True}]
    target_benign = [{"task_id": "BENIGN-001", "name": "Task 1", "passed": False, "reason": "Blocked by policy"}]  # Utility regression!

    report = detect_regressions(
        baseline_attacks=baseline_attacks,
        target_attacks=target_attacks,
        baseline_benign=baseline_benign,
        target_benign=target_benign,
    )

    assert report.has_regressions is True
    assert len(report.security_regressions) == 1
    assert len(report.utility_regressions) == 1


@pytest.mark.asyncio
async def test_matrix_runner_execution() -> None:
    """Run a small 2-combo matrix test to verify row output and tradeoff calculations."""
    runner = EvalMatrixRunner()

    test_combos = [
        {"id": "c_none", "name": "Unprotected", "defenses": []},
        {"id": "c_policy", "name": "Policy Engine", "defenses": ["policy_engine"]},
    ]

    result = await runner.run_matrix(
        campaign_id="test-matrix-campaign",
        combos=test_combos,
        include_benign=True,
        budget_k=2,
    )

    assert result.total_combos_tested == 2
    assert len(result.rows) == 2
    assert len(result.tradeoff_dataset) == 2
    assert result.recommended_combo != ""
    assert result.rows[0].resilience_score >= 0.0

