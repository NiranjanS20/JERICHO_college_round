"""
Pydantic v2 schemas for AgentBreak API requests, responses, and SSE events.

All ORM-facing response schemas set ``from_attributes = True`` so they can
be constructed directly from SQLAlchemy model instances.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ───────────────────────────────────────────────────────────────
# Oracle
# ───────────────────────────────────────────────────────────────
class OracleVerdict(BaseModel):
    """Classifier judgement on whether an attack succeeded."""

    success: bool = False
    violated_policies: list[str] = Field(default_factory=list)
    violated_policy: str | None = None
    severity: str = "none"
    evidence: Any = Field(default_factory=list)
    partial_score: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


# ───────────────────────────────────────────────────────────────
# Campaign
# ───────────────────────────────────────────────────────────────
class CampaignCreate(BaseModel):
    """Payload for creating a new campaign."""

    goals: list[str]
    categories: list[str] = Field(default_factory=list)
    budget_per_goal: int = 10
    defense_ids: list[str] = Field(default_factory=list)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)


class CampaignResponse(BaseModel):
    """Full campaign representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    status: str
    goals: list[str]
    categories: list[str]
    budget_per_goal: int
    defense_ids: list[str]
    config_snapshot: dict[str, Any]


# ───────────────────────────────────────────────────────────────
# TraceStep
# ───────────────────────────────────────────────────────────────
class TraceStepResponse(BaseModel):
    """A single trace step in a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    attack_id: str
    step_index: int
    role: str
    content: str
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None
    is_malicious: bool = False
    timestamp: datetime


# ───────────────────────────────────────────────────────────────
# Attack
# ───────────────────────────────────────────────────────────────
class AttackSummaryResponse(BaseModel):
    """Lightweight attack record for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    goal: str
    category: str
    strategy: str
    iteration: int
    status: str
    partial_score: float
    best_in_chain: bool
    created_at: datetime


class AttackResponse(BaseModel):
    """Full attack record including trace steps and oracle verdict."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    goal: str
    category: str
    strategy: str
    iteration: int
    injection_point: str
    payload: str
    status: str
    oracle_verdict: OracleVerdict | None = None
    partial_score: float
    best_in_chain: bool
    created_at: datetime
    trace_steps: list[TraceStepResponse] = Field(default_factory=list)


# ───────────────────────────────────────────────────────────────
# Replay
# ───────────────────────────────────────────────────────────────
class ReplayRequest(BaseModel):
    """Request to statistically replay an attack."""

    attack_id: str
    n_runs: int = 10
    defense_ids: list[str] = Field(default_factory=list)


class ReplayResponse(BaseModel):
    """Statistical replay results."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    attack_id: str
    n_runs: int
    successes: int
    success_rate: float
    wilson_ci_low: float
    wilson_ci_high: float
    defenses_used: list[str]
    created_at: datetime


# ───────────────────────────────────────────────────────────────
# Defense evaluation
# ───────────────────────────────────────────────────────────────
class DefenseInfo(BaseModel):
    """Descriptor for a single defense layer."""

    id: str
    name: str
    description: str = ""
    enabled: bool = True


class DefenseEvalRequest(BaseModel):
    """Request to evaluate a set of defenses against a campaign."""

    campaign_id: str
    defense_combos: list[list[str]]


class EvalMatrixRequest(BaseModel):
    """Request for a full evaluation matrix."""

    campaign_id: str
    defense_combos: list[list[str]]
    include_benign: bool = True


class EvalMatrixResponse(BaseModel):
    """One row of the defense evaluation matrix."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    defense_combo: list[str]
    attack_success_rate: float
    benign_pass_rate: float
    regressions: dict[str, Any] | None = None
    adaptive_asr: float
    static_asr: float
    created_at: datetime


# ───────────────────────────────────────────────────────────────
# Metrics
# ───────────────────────────────────────────────────────────────
class MetricsSummaryResponse(BaseModel):
    """Aggregated metrics for a campaign."""

    campaign_id: str
    total_attacks: int = 0
    successful_attacks: int = 0
    failed_attacks: int = 0
    error_attacks: int = 0
    overall_asr: float = 0.0
    avg_partial_score: float = 0.0
    category_breakdown: dict[str, dict[str, Any]] = Field(default_factory=dict)
    strategy_breakdown: dict[str, dict[str, Any]] = Field(default_factory=dict)


# ───────────────────────────────────────────────────────────────
# Attack graph (visualisation)
# ───────────────────────────────────────────────────────────────
class AttackGraphNode(BaseModel):
    """A node in the attack-trace graph."""

    id: str
    type: str
    label: str
    data: dict[str, Any] = Field(default_factory=dict)
    # data typically contains: content, tool_name, tool_args,
    # is_malicious, step_index


class AttackGraphEdge(BaseModel):
    """An edge in the attack-trace graph."""

    id: str
    source: str
    target: str
    is_malicious_path: bool = False
    label: str = ""


class AttackGraphResponse(BaseModel):
    """Full attack-trace graph for visualisation."""

    nodes: list[AttackGraphNode] = Field(default_factory=list)
    edges: list[AttackGraphEdge] = Field(default_factory=list)


# ───────────────────────────────────────────────────────────────
# SSE event schemas
# ───────────────────────────────────────────────────────────────
class AttackStartedEvent(BaseModel):
    """Emitted when a new attack attempt begins."""

    event: str = "attack_started"
    attack_id: str
    campaign_id: str
    goal: str
    strategy: str
    iteration: int


class StepEvent(BaseModel):
    """Emitted for each conversation step (message sent/received)."""

    event: str = "step"
    attack_id: str
    step_index: int
    role: str
    content: str


class ToolCallEvent(BaseModel):
    """Emitted when the victim agent calls a tool."""

    event: str = "tool_call"
    attack_id: str
    step_index: int
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    tool_result: dict[str, Any] | None = None
    is_malicious: bool = False


class OracleVerdictEvent(BaseModel):
    """Emitted when the oracle returns a judgement."""

    event: str = "oracle_verdict"
    attack_id: str
    verdict: OracleVerdict


class IterationScoreEvent(BaseModel):
    """Emitted after each iteration is scored."""

    event: str = "iteration_score"
    attack_id: str
    iteration: int
    partial_score: float
    best_in_chain: bool


class AttackFinishedEvent(BaseModel):
    """Emitted when an attack attempt ends."""

    event: str = "attack_finished"
    attack_id: str
    status: str
    partial_score: float
    oracle_verdict: OracleVerdict | None = None
