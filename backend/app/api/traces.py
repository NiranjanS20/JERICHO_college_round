"""
Traces API routes for AgentBreak.

Provides trace graph construction (nodes & edges formatted for React Flow)
and step-by-step forensic inspection of attacks.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Attack, TraceStep
from app.schemas import AttackGraphEdge, AttackGraphNode, AttackGraphResponse

router = APIRouter(prefix="/api/traces", tags=["traces"])


@router.get("/{attack_id}", response_model=AttackGraphResponse)
async def get_attack_trace_graph(
    attack_id: str,
    db: AsyncSession = Depends(get_db),
) -> AttackGraphResponse:
    """Build React Flow compatible attack graph with malicious path highlighting."""
    stmt = (
        select(Attack)
        .options(selectinload(Attack.trace_steps))
        .where(Attack.id == attack_id)
    )
    result = await db.execute(stmt)
    attack = result.scalar_one_or_none()
    if not attack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attack '{attack_id}' not found.",
        )

    # Sort steps by step_index
    steps: list[TraceStep] = sorted(attack.trace_steps, key=lambda s: s.step_index)

    nodes: list[AttackGraphNode] = []
    edges: list[AttackGraphEdge] = []
    malicious_node_ids: set[str] = set()

    for idx, step in enumerate(steps):
        node_id = f"node-{step.id}"

        # Classify node type
        if step.role == "user":
            node_type = "user_input"
            label = "Adversarial Prompt" if step.is_malicious else "User Input"
        elif step.role == "tool_call":
            if step.tool_name in ("search_docs", "read_email"):
                node_type = "retrieved_doc"
                label = f"Retrieved ({step.tool_name})"
            else:
                node_type = "tool_call"
                label = f"Tool Call: {step.tool_name}"
        elif step.role == "assistant":
            if step.is_malicious or attack.status == "success":
                node_type = "leak"
                label = "Policy Breach / Leak"
            else:
                node_type = "llm_decision"
                label = "Assistant Response"
        else:
            node_type = "step"
            label = f"{step.role.capitalize()}"

        node_data: dict[str, Any] = {
            "content": step.content,
            "role": step.role,
            "tool_name": step.tool_name,
            "tool_args": step.tool_args,
            "tool_result": step.tool_result,
            "is_malicious": step.is_malicious,
            "step_index": step.step_index,
        }

        nodes.append(
            AttackGraphNode(
                id=node_id,
                type=node_type,
                label=label,
                data=node_data,
            )
        )

        if step.is_malicious or node_type == "leak":
            malicious_node_ids.add(node_id)

    # Construct edges connecting sequential steps
    for i in range(1, len(nodes)):
        src = nodes[i - 1]
        tgt = nodes[i]
        is_mal = src.id in malicious_node_ids or tgt.id in malicious_node_ids
        edges.append(
            AttackGraphEdge(
                id=f"e-{src.id}-{tgt.id}",
                source=src.id,
                target=tgt.id,
                is_malicious_path=is_mal,
                label="Malicious Flow" if is_mal else "Normal Flow",
            )
        )

    return AttackGraphResponse(nodes=nodes, edges=edges)

