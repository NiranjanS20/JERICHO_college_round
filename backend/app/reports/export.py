"""
Report generation and export module for AgentBreak.

Supports structured JSON export and clean, printable HTML/PDF-ready security reports
detailing attack discovery, oracle verdicts, OWASP categories, and defense matrix evaluations.
"""

from __future__ import annotations

import json
from typing import Any
from app.models import Campaign


def export_campaign_json(campaign: Campaign) -> dict[str, Any]:
    """Generate a full JSON export of a completed campaign and its findings."""
    attacks_data = []
    total_attacks = len(campaign.attacks)
    successful_attacks = 0

    category_counts: dict[str, dict[str, int]] = {}
    strategy_counts: dict[str, dict[str, int]] = {}

    for attack in campaign.attacks:
        is_success = attack.status == "success"
        if is_success:
            successful_attacks += 1

        cat = attack.category
        if cat not in category_counts:
            category_counts[cat] = {"total": 0, "successful": 0}
        category_counts[cat]["total"] += 1
        if is_success:
            category_counts[cat]["successful"] += 1

        strat = attack.strategy
        if strat not in strategy_counts:
            strategy_counts[strat] = {"total": 0, "successful": 0}
        strategy_counts[strat]["total"] += 1
        if is_success:
            strategy_counts[strat]["successful"] += 1

        attacks_data.append({
            "id": attack.id,
            "goal": attack.goal,
            "category": attack.category,
            "strategy": attack.strategy,
            "iteration": attack.iteration,
            "injection_point": attack.injection_point,
            "status": attack.status,
            "payload": attack.payload,
            "oracle_verdict": attack.oracle_verdict,
            "partial_score": attack.partial_score,
            "best_in_chain": attack.best_in_chain,
            "created_at": attack.created_at.isoformat() if attack.created_at else None,
            "steps_count": len(attack.trace_steps) if "trace_steps" in attack.__dict__ else 0,
        })

    eval_matrix_data = []
    for em in getattr(campaign, "eval_matrix_results", []):
        eval_matrix_data.append({
            "defense_combo": em.defense_combo,
            "attack_success_rate": em.attack_success_rate,
            "benign_pass_rate": em.benign_pass_rate,
            "adaptive_asr": em.adaptive_asr,
            "static_asr": em.static_asr,
            "regressions": em.regressions,
        })

    overall_asr = (successful_attacks / total_attacks) if total_attacks > 0 else 0.0

    return {
        "campaign_id": campaign.id,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "status": campaign.status,
        "config_snapshot": campaign.config_snapshot or {},
        "goals": campaign.goals or [],
        "categories": campaign.categories or [],
        "budget_per_goal": campaign.budget_per_goal,
        "defense_ids": campaign.defense_ids or [],
        "summary": {
            "total_attacks": total_attacks,
            "successful_attacks": successful_attacks,
            "overall_asr": round(overall_asr, 3),
            "category_breakdown": category_counts,
            "strategy_breakdown": strategy_counts,
        },
        "attacks": attacks_data,
        "eval_matrix": eval_matrix_data,
    }


def export_campaign_html(campaign: Campaign) -> str:
    """Generate a standalone, modern HTML security evaluation report."""
    data = export_campaign_json(campaign)
    summary = data["summary"]

    attacks_rows = []
    for a in data["attacks"]:
        badge_color = "#9D3B31" if a["status"] == "success" else "#2E6A4F"
        verdict_str = "None"
        if a["oracle_verdict"] and a["oracle_verdict"].get("violated_policies"):
            verdict_str = ", ".join(a["oracle_verdict"]["violated_policies"])

        attacks_rows.append(f"""
        <tr>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA; font-family: monospace; font-size: 12px;">{a['id'][:8]}</td>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA;">{a['goal']}</td>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA;"><span style="background: #F9F8F6; border: 1px solid #F2F0EA; padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #1C1C1A;">{a['category']}</span></td>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA; font-size: 12px;">{a['strategy']}</td>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA; text-align: center;"><span style="color: white; background: {badge_color}; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">{a['status'].upper()}</span></td>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA; font-size: 12px; color: #9D3B31;">{verdict_str}</td>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA; text-align: right; font-weight: 600;">{a['partial_score']:.2f}</td>
        </tr>
        """)

    matrix_rows = []
    for m in data["eval_matrix"]:
        combo_str = " + ".join(m["defense_combo"]) if m["defense_combo"] else "None (Baseline)"
        matrix_rows.append(f"""
        <tr>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA; font-weight: 500;">{combo_str}</td>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA; text-align: center; font-weight: 600; color: {'#9D3B31' if m['attack_success_rate'] > 0.3 else '#2E6A4F'};">{m['attack_success_rate'] * 100:.1f}%</td>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA; text-align: center; font-weight: 600; color: {'#2E6A4F' if m['benign_pass_rate'] >= 0.8 else '#9D3B31'};">{m['benign_pass_rate'] * 100:.1f}%</td>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA; text-align: center;">{m['adaptive_asr'] * 100:.1f}%</td>
          <td style="padding: 10px; border-bottom: 1px solid #F2F0EA; text-align: center;">{m['static_asr'] * 100:.1f}%</td>
        </tr>
        """)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AgentBreak Red-Team Security Assessment Report</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
    body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #1C1C1A; background: #F9F8F6; }}
    h1, h2, h3 {{ font-family: 'Playfair Display', serif; color: #1C1C1A; font-weight: 700; }}
    .header {{ border-bottom: 1px solid #F2F0EA; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: flex-end; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600; background: #FFFFFF; border: 1px solid #F2F0EA; color: #1C1C1A; }}
    .stat-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 30px; }}
    .stat-card {{ background: #FFFFFF; border: 1px solid #F2F0EA; border-radius: 8px; padding: 18px; text-align: center; }}
    .stat-val {{ font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 700; color: #1C1C1A; margin-top: 4px; }}
    .stat-label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #1C1C1A; opacity: 0.7; font-weight: 600; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13px; background: #FFFFFF; border: 1px solid #F2F0EA; border-radius: 8px; overflow: hidden; }}
    th {{ background: #F9F8F6; padding: 10px; text-align: left; font-weight: 600; color: #1C1C1A; border-bottom: 1px solid #F2F0EA; }}
    .section {{ margin-bottom: 40px; }}
    @media print {{ body {{ margin: 20px; background: #FFFFFF; }} table {{ border: 1px solid #1C1C1A; }} th, td {{ border-bottom: 1px solid #1C1C1A; }} }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <span class="badge">AGENTBREAK RED-TEAM ASSESSMENT</span>
      <h1 style="margin: 8px 0 4px 0;">Acme Corp Assistant Security Audit</h1>
      <p style="color: #1C1C1A; opacity: 0.8; margin: 0; font-size: 14px;">Campaign ID: <code>{data['campaign_id']}</code> | Status: <strong>{data['status'].upper()}</strong></p>
    </div>
    <div style="text-align: right; color: #1C1C1A; opacity: 0.8; font-size: 13px;">
      Generated: {data['created_at'] or 'Recent'}<br>
      Objective Oracle: <strong>CANARY &amp; POLICY VERIFIED</strong>
    </div>
  </div>

  <div class="stat-grid">
    <div class="stat-card">
      <div class="stat-label">Total Attacks</div>
      <div class="stat-val">{summary['total_attacks']}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Successful Breaches</div>
      <div class="stat-val" style="color: #9D3B31;">{summary['successful_attacks']}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Attack Success Rate</div>
      <div class="stat-val" style="color: {'#9D3B31' if summary['overall_asr'] > 0.3 else '#2E6A4F'};">{summary['overall_asr'] * 100:.1f}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Active Defenses Tested</div>
      <div class="stat-val">{len(data['defense_ids'])}</div>
    </div>
  </div>

  <div class="section">
    <h2>1. Executive Summary &amp; Scope</h2>
    <p style="line-height: 1.6; color: #1C1C1A; opacity: 0.9;">
      AgentBreak conducted an automated defensive red-team engagement against the sandboxed Acme Corp internal assistant.
      The attack engine leveraged adaptive mutators and static baselines targeting LLM-specific vulnerabilities including
      Direct Prompt Injection, Indirect Retrieval Smuggling, Tool Privilege Abuse, and Cross-Session Memory Poisoning.
      Every breach was determined objectively by cryptographic canary leak verification or deterministic policy violations.
    </p>
  </div>

  <div class="section">
    <h2>2. Defense Matrix Evaluation (Security vs. Utility)</h2>
    <table>
      <thead>
        <tr>
          <th>Defense Configuration</th>
          <th style="text-align: center;">Attack Success (ASR)</th>
          <th style="text-align: center;">Benign Utility</th>
          <th style="text-align: center;">Adaptive ASR</th>
          <th style="text-align: center;">Static ASR</th>
        </tr>
      </thead>
      <tbody>
        {"".join(matrix_rows) if matrix_rows else '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #1C1C1A; opacity: 0.5;">No matrix evaluated for this campaign.</td></tr>'}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>3. Findings Log &amp; Exploit Traces</h2>
    <table>
      <thead>
        <tr>
          <th>Attack ID</th>
          <th>Goal</th>
          <th>OWASP Category</th>
          <th>Strategy</th>
          <th style="text-align: center;">Status</th>
          <th>Policy Violation</th>
          <th style="text-align: right;">Progress Score</th>
        </tr>
      </thead>
      <tbody>
        {"".join(attacks_rows) if attacks_rows else '<tr><td colspan="7" style="padding: 12px; text-align: center; color: #1C1C1A; opacity: 0.5;">No attacks recorded.</td></tr>'}
      </tbody>
    </table>
  </div>
</body>
</html>
"""
    return html
