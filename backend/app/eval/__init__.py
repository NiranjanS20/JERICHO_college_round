"""
Evaluation and matrix benchmarking package for AgentBreak.
"""

from __future__ import annotations

from app.eval.benign_tasks import BENIGN_TASKS, BenignSuiteResult, BenignTask, evaluate_benign_task, run_benign_suite
from app.eval.matrix import CURATED_DEFENSE_COMBINATIONS, EvalMatrixRunResult, EvalMatrixRunner, MatrixRowResult
from app.eval.metrics import DefenseTradeoffPoint, compute_adaptive_delta, compute_tradeoff_point
from app.eval.regression import RegressionReport, detect_regressions

__all__ = [
    "BENIGN_TASKS",
    "BenignTask",
    "BenignSuiteResult",
    "evaluate_benign_task",
    "run_benign_suite",
    "CURATED_DEFENSE_COMBINATIONS",
    "EvalMatrixRunner",
    "EvalMatrixRunResult",
    "MatrixRowResult",
    "DefenseTradeoffPoint",
    "compute_tradeoff_point",
    "compute_adaptive_delta",
    "RegressionReport",
    "detect_regressions",
]

