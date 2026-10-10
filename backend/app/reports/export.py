"""
Report generation and export module for AgentBreak.

Supports structured JSON export and clean, printable HTML/PDF-ready security reports
detailing attack discovery, oracle verdicts, OWASP categories, and defense matrix evaluations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader
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
    """Generate a standalone, modern HTML security evaluation report using Jinja2."""
    data = export_campaign_json(campaign)
    
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    template = env.get_template("report.html.jinja")
    
    return template.render(
        data=data,
        summary=data["summary"],
        attacks_rows=data["attacks"],
        matrix_rows=data["eval_matrix"]
    )
