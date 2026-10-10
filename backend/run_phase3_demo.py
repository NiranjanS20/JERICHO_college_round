"""
Phase 3 Demonstration Script: Pluggable Defenses, Benign Tasks & Evaluation Matrix.

Demonstrates:
1. The 5 pluggable defense layers: Delimiting, Hierarchy Prompt, Policy Engine, Injection Classifier, Human Approval.
2. The 20 benign workflow tasks measuring baseline utility preservation.
3. The full ATTACKS x DEFENSES evaluation matrix, regression detector, and security vs utility tradeoff dataset.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db import init_db
from app.defenses import list_defense_metadata
from app.eval import BENIGN_TASKS, CURATED_DEFENSE_COMBINATIONS, EvalMatrixRunner, run_benign_suite
from app.oracle.oracle import Oracle
from app.victim.agent import VictimAgent


async def run_phase3_demo() -> None:
    print("=" * 80)
    print("  AgentBreak Phase 3 Demo: Pluggable Defenses Stack & Evaluation Matrix")
    print("=" * 80)

    await init_db()

    # 1. Display Defense Layers Catalog
    print("\n[1/3] Pluggable Defense Stack (5 Independently Toggleable Layers):")
    defenses = list_defense_metadata()
    for d in defenses:
        print(f"      • [{d['id']}] {d['name']}")
        print(f"        {d['description']}")

    # 2. Run Benign Utility Tasks
    print("\n[2/3] Evaluating Benign Task Suite (20 Real-World Employee Workflows)...")
    oracle = Oracle()
    async def benign_runner(prompt: str):
        victim = VictimAgent()
        return await victim.run(prompt)

    benign_results = await run_benign_suite(benign_runner, oracle=oracle)
    print(f"      Total Benign Tasks     : {benign_results.total_tasks}")
    print(f"      Tasks Passed           : {benign_results.passed_tasks}")
    print(f"      Baseline Utility Rate  : {benign_results.utility_rate * 100:.1f}%")
    print(f"      Sample Tasks Evaluated :")
    for task_res in benign_results.results[:4]:
        status_symbol = "✅" if task_res.passed else "❌"
        print(f"        {status_symbol} [{task_res.task_id}] {task_res.name}: {task_res.reason}")

    # 3. Execute ATTACKS x DEFENSES Evaluation Matrix
    print("\n[3/3] Executing Attacks × Defenses Evaluation Matrix across 7 Combinations...")
    matrix_runner = EvalMatrixRunner(oracle=oracle)

    matrix_res = await matrix_runner.run_matrix(
        campaign_id="demo-campaign-003",
        combos=CURATED_DEFENSE_COMBINATIONS,
        include_benign=True,
        budget_k=2,
    )

    print("\n" + "-" * 80)
    print(f"{'DEFENSE CONFIGURATION':<36} | {'ASR':<8} | {'UTILITY':<8} | {'RESILIENCE':<10}")
    print("-" * 80)

    for row in matrix_res.rows:
        asr_str = f"{row.attack_success_rate * 100:.1f}%"
        util_str = f"{row.benign_pass_rate * 100:.1f}%"
        resil_str = f"{row.resilience_score * 100:.1f}%"
        print(f"{row.combo_name:<36} | {asr_str:<8} | {util_str:<8} | {resil_str:<10}")

    print("-" * 80)
    print(f"\n      Recommended Defense Stack : {matrix_res.recommended_combo}")
    print("      Security vs. Utility Tradeoff Dataset (for Recharts):")
    for pt in matrix_res.tradeoff_dataset:
        print(f"        - {pt['name']:<34} -> ASR: {pt['asr']:>5.1f}% | Utility: {pt['utility']:>5.1f}% | Resilience: {pt['resilience']:>5.1f}%")

    print("\n" + "=" * 80)
    print("  Phase 3 Complete: Defenses Stack, Benign Suite & Eval Matrix Verified!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_phase3_demo())

