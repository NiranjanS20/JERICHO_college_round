#!/usr/bin/env python3
"""
CI/CD Regression Suite Runner for AgentBreak (Phase 6).

Replays confirmed exploits stored in regression_set/ against the victim
agent with active defenses. Exits with non-zero status code if any
previously fixed vulnerability is reintroduced.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Setup paths
root_dir = Path(__file__).resolve().parents[1]
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.defenses import DEFENSE_REGISTRY
from app.oracle.oracle import Oracle, OracleVerdict
from app.victim.agent import AgentResult, VictimAgent


async def main() -> int:
    print("================================================================")
    print("  AgentBreak CI/CD Security Regression Suite Runner")
    print("================================================================")

    reg_dir = root_dir / "regression_set"
    scenarios = list(reg_dir.glob("*.json"))

    if not scenarios:
        print("[!] No regression scenarios found in regression_set/")
        return 0

    print(f"Loaded {len(scenarios)} frozen vulnerability regression test cases.\n")

    # Instantiate all active defenses for the hardened agent
    active_defenses = [
        DEFENSE_REGISTRY["hierarchy_prompt"](),
        DEFENSE_REGISTRY["policy_engine"](),
        DEFENSE_REGISTRY["delimiting"](),
    ]
    victim = VictimAgent(defenses=active_defenses)
    oracle = Oracle()

    regressions = 0

    for scen_file in scenarios:
        with open(scen_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        scen_id = data.get("scenario_id")
        name = data.get("name")
        payload = data.get("payload")

        print(f"[RUN] {scen_id}: {name}")
        agent_result: AgentResult = await victim.run(payload)

        messages = [
            {"role": "user", "content": payload},
            {"role": "assistant", "content": agent_result.final_answer},
        ]
        tools = [{"tool_name": c.tool_name, "args": c.args, "result": c.result} for c in agent_result.tool_calls]
        verdict: OracleVerdict = oracle.evaluate(messages, tools, agent_result.final_answer)

        if verdict.success:
            print(f"      ❌ REGRESSION DETECTED: Exploit succeeded! Violations: {verdict.violated_policies}")
            regressions += 1
        else:
            print("      ✅ BLOCKED: Defenses successfully prevented exploit.")

    print("\n----------------------------------------------------------------")
    if regressions > 0:
        print(f"FAILED: {regressions} security regressions detected!")
        return 1
    else:
        print(f"PASSED: All {len(scenarios)} regression test cases successfully blocked.")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
