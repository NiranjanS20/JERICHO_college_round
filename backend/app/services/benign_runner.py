"""
Benign task runner service for AgentBreak.

Executes legitimate workflow tasks against a configured VictimAgent to verify
utility retention, ensuring security defenses do not disrupt benign operations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.defenses.base import Defense
from app.eval.benign_tasks import (
    BENIGN_TASKS,
    BenignTask,
    BenignTaskResult,
    evaluate_benign_task,
)
from app.oracle.oracle import Oracle
from app.scenarios.case_studies import CASE_STUDIES
from app.victim.agent import VictimAgent

logger = logging.getLogger(__name__)


@dataclass
class BenignRunSummary:
    """Summary of benign utility evaluation."""

    total_tasks: int
    passed_tasks: int
    utility_rate: float
    results: list[dict[str, Any]] = field(default_factory=list)


class BenignTaskRunner:
    """Orchestrates execution of benign tasks to measure utility retention."""

    def __init__(self, oracle: Oracle | None = None) -> None:
        self.oracle = oracle or Oracle()

    async def run_for_case_study(
        self,
        case_study_id: str,
        defenses: list[Defense] | None = None,
        caller_role: str = "employee",
        allowed_tools: list[str] | None = None,
        model: str | None = None,
    ) -> BenignRunSummary:
        """Run benign tasks matching the case study and return utility metrics."""
        cs = next((c for c in CASE_STUDIES if c.id == case_study_id), None)
        task_ids = cs.benign_task_ids if cs else ["BENIGN-001"]

        # Select matching tasks or fallback to all relevant tasks
        matching_tasks = [t for t in BENIGN_TASKS if t.id in task_ids]
        if not matching_tasks:
            matching_tasks = BENIGN_TASKS[:2]

        victim = VictimAgent(
            defenses=defenses,
            case_study_id=case_study_id,
            caller_role=caller_role,
            allowed_tools=allowed_tools,
            model=model,
        )

        results: list[dict[str, Any]] = []
        passed_count = 0

        for task in matching_tasks:
            victim.reset()
            agent_result = await victim.run(task.prompt)
            eval_res: BenignTaskResult = evaluate_benign_task(task, agent_result, oracle=self.oracle)

            if eval_res.passed:
                passed_count += 1

            results.append({
                "task_id": eval_res.task_id,
                "task_name": eval_res.name,
                "passed": eval_res.passed,
                "tools_called": eval_res.tools_called,
                "missing_tools": eval_res.missing_tools,
                "missing_keywords": eval_res.missing_keywords,
                "policy_violated": eval_res.policy_violated,
                "details": eval_res.reason,
            })

        utility = round(passed_count / len(matching_tasks), 4) if matching_tasks else 1.0

        return BenignRunSummary(
            total_tasks=len(matching_tasks),
            passed_tasks=passed_count,
            utility_rate=utility,
            results=results,
        )
