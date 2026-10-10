"""
AgentBreak Phase 4 Demonstration Script:
REST API, SSE Live Event Streaming, Demo Cache, and Report Generation.

Executes a live API workout using httpx ASGITransport against the FastAPI app.
"""

from __future__ import annotations

import asyncio
import sys
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db import init_db


async def main() -> None:
    print("=" * 80)
    print("  AgentBreak Phase 4 Demo: REST API, SSE Streaming, Demo Cache & Reports")
    print("=" * 80)

    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        print("\n[1/6] Querying /api/health ...")
        res = await client.get("/api/health")
        print(f"      Status: {res.status_code} | Data: {res.json()}")

        # 2. Demo cache loading
        print("\n[2/6] Triggering POST /api/demo/load (Zero-API-cost offline demo)...")
        res = await client.post("/api/demo/load")
        load_info = res.json()
        print(f"      Status: {res.status_code}")
        print(f"      Loaded Campaign ID: {load_info['campaign_id']}")
        print(f"      Attacks Ingested  : {load_info['attacks_loaded']}")
        print(f"      Eval Matrix Rows  : {load_info['eval_matrix_rows_loaded']}")

        campaign_id = load_info["campaign_id"]

        # 3. List campaigns and attacks
        print(f"\n[3/6] Querying Campaign & Attack Traces for '{campaign_id}' ...")
        c_res = await client.get(f"/api/campaigns/{campaign_id}")
        camp = c_res.json()
        print(f"      Campaign Goals   : {len(camp['goals'])} target objectives")
        print(f"      Execution Status : {camp['status'].upper()}")

        a_res = await client.get(f"/api/attacks?campaign_id={campaign_id}")
        attacks = a_res.json()
        print(f"      Attacks Recorded : {len(attacks)}")
        first_atk = attacks[0]
        print(f"      Sample Attack    : [{first_atk['id']}] Strategy: {first_atk['strategy']} | Status: {first_atk['status'].upper()}")

        # 4. Attack graph generation for React Flow
        print(f"\n[4/6] Generating React Flow Attack Graph for Attack '{first_atk['id']}' ...")
        g_res = await client.get(f"/api/traces/{first_atk['id']}")
        graph = g_res.json()
        print(f"      Graph Nodes      : {len(graph['nodes'])} nodes ({[n['type'] for n in graph['nodes']]})")
        print(f"      Graph Edges      : {len(graph['edges'])} edges (Malicious path flagged: {any(e['is_malicious_path'] for e in graph['edges'])})")

        # 5. Statistical Replay with Wilson CI
        print(f"\n[5/6] Executing POST /api/attacks/{first_atk['id']}/replay (N=5 runs)...")
        rep_res = await client.post(
            f"/api/attacks/{first_atk['id']}/replay",
            json={"attack_id": first_atk["id"], "n_runs": 5, "defense_ids": []},
        )
        rep = rep_res.json()
        print(f"      Replay Trials    : {rep['n_runs']}")
        print(f"      Empirical ASR    : {rep['success_rate'] * 100:.1f}% ({rep['successes']}/{rep['n_runs']} breached)")
        print(f"      Wilson 95% CI    : [{rep['wilson_ci_low']:.3f}, {rep['wilson_ci_high']:.3f}]")

        # 6. Report Export
        print(f"\n[6/6] Generating Executive Assessment Report for '{campaign_id}' ...")
        rep_json = await client.get(f"/api/reports/{campaign_id}?format=json")
        summary = rep_json.json()["summary"]
        print(f"      Report Metrics   : Overall ASR {summary['overall_asr'] * 100:.1f}% across {summary['total_attacks']} attacks")
        print(f"      OWASP Categories : {list(summary['category_breakdown'].keys())}")

        rep_html = await client.get(f"/api/reports/{campaign_id}?format=html")
        print(f"      Printable HTML   : {len(rep_html.text)} bytes generated with styled executive tables and findings.")

    print("\n" + "=" * 80)
    print("  Phase 4 Complete: REST API, SSE Live Streams, Demo Cache & Reports Ready!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

