"""
Replay engine — deterministically re-run stored attacks.

Re-executes an attack N times (default 10) against the victim agent with
deterministic mocked tools, reporting empirical success rate and a
Wilson 95% confidence interval. Supports replaying against a defended victim.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.oracle.oracle import Oracle, OracleVerdict
from app.victim.agent import VictimAgent


# ---------------------------------------------------------------------------
# Replay result
# ---------------------------------------------------------------------------

@dataclass
class ReplayResult:
    """Aggregated result of replaying an attack *n* times."""

    attack_id: str
    n_runs: int
    successes: int
    success_rate: float
    wilson_ci_low: float
    wilson_ci_high: float
    defenses_used: list[str] = field(default_factory=list)
    individual_results: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Replay engine
# ---------------------------------------------------------------------------

class ReplayEngine:
    """Re-run stored attacks to measure reproducibility and defense efficacy."""

    def __init__(self, oracle: Oracle | None = None) -> None:
        self._oracle = oracle or Oracle()

    async def replay(
        self,
        attack_id: str,
        payload: str | None = None,
        n_runs: int = 10,
        defenses: list[Any] | None = None,
        session: AsyncSession | None = None,
    ) -> ReplayResult:
        """Replay an attack ``n_runs`` times.

        Parameters
        ----------
        attack_id:
            Identifier of the attack to replay.
        payload:
            The raw attack payload. If None and a database session is provided,
            loads the payload from the Attack table.
        n_runs:
            Number of replay executions (default 10).
        defenses:
            Optional list of defense instances or defense IDs.
        session:
            Optional async database session to fetch stored attack records.
        """
        target_payload = payload

        # If payload not provided directly, attempt to fetch from DB
        if target_payload is None and session is not None:
            from app.models import Attack
            stmt = select(Attack).where(Attack.id == attack_id)
            res = await session.execute(stmt)
            attack_record = res.scalar_one_or_none()
            if attack_record:
                target_payload = attack_record.payload

        if target_payload is None:
            raise ValueError(
                f"No payload provided for replay of attack {attack_id!r} "
                "and no matching database record found."
            )

        successes = 0
        individual_results: list[dict[str, Any]] = []

        defense_names: list[str] = []
        if defenses:
            for d in defenses:
                if hasattr(d, "id"):
                    defense_names.append(d.id)
                elif isinstance(d, str):
                    defense_names.append(d)
                else:
                    defense_names.append(d.__class__.__name__)

        for run_idx in range(n_runs):
            # Instantiate fresh victim agent with defenses
            victim = VictimAgent(defenses=defenses)
            agent_result = await victim.run(target_payload)

            # Evaluate with Oracle
            messages_for_oracle = [
                {"role": "user", "content": target_payload},
                {"role": "assistant", "content": agent_result.final_answer},
            ]
            tools_for_oracle = [
                {"tool_name": c.tool_name, "args": c.args, "result": c.result}
                for c in agent_result.tool_calls
            ]
            verdict: OracleVerdict = self._oracle.evaluate(
                messages=messages_for_oracle,
                tool_calls=tools_for_oracle,
                final_answer=agent_result.final_answer,
            )

            if verdict.success:
                successes += 1

            individual_results.append({
                "run_index": run_idx + 1,
                "success": verdict.success,
                "violated_policies": verdict.violated_policies,
                "severity": verdict.severity,
                "partial_score": verdict.partial_score,
                "final_answer_preview": agent_result.final_answer[:100],
            })

        success_rate = round(successes / n_runs, 4) if n_runs > 0 else 0.0
        ci_low, ci_high = self.wilson_score_interval(successes, n_runs)

        return ReplayResult(
            attack_id=attack_id,
            n_runs=n_runs,
            successes=successes,
            success_rate=success_rate,
            wilson_ci_low=ci_low,
            wilson_ci_high=ci_high,
            defenses_used=defense_names,
            individual_results=individual_results,
        )

    @staticmethod
    def wilson_score_interval(
        successes: int,
        total: int,
        confidence: float = 0.95,
    ) -> tuple[float, float]:
        """Compute the Wilson score confidence interval for a proportion.

        Parameters
        ----------
        successes:
            Number of successful outcomes (attacks that succeeded).
        total:
            Total number of trials.
        confidence:
            Desired confidence level (default 0.95).

        Returns
        -------
        tuple[float, float]
            ``(lower_bound, upper_bound)`` clamped to [0, 1].
        """
        if total <= 0:
            return (0.0, 0.0)

        _Z_TABLE: dict[float, float] = {
            0.90: 1.6449,
            0.95: 1.96,
            0.99: 2.5758,
        }
        z = _Z_TABLE.get(confidence, 1.96)

        n = total
        p_hat = successes / n
        z2 = z * z

        # Wilson score center
        center = (p_hat + z2 / (2 * n)) / (1 + z2 / n)

        # Wilson score margin
        margin = (
            z
            * math.sqrt((p_hat * (1 - p_hat) / n) + (z2 / (4 * n * n)))
            / (1 + z2 / n)
        )

        lower = round(max(0.0, center - margin), 4)
        upper = round(min(1.0, center + margin), 4)

        return (lower, upper)
