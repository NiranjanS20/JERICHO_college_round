"""
Pydantic v2 schemas for AgentBreak API requests, responses, and SSE events.

All ORM-facing response schemas set ``from_attributes = True`` so they can
be constructed directly from SQLAlchemy model instances.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ───────────────────────────────────────────────────────────────
# Oracle
# ───────────────────────────────────────────────────────────────
class OracleVerdict(StrictBaseModel):
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
class CampaignCreate(StrictBaseModel):
    """Payload for creating a new campaign."""

    goals: list[str]
    categories: list[str] = Field(default_factory=list)
    budget_per_goal: int = 10
    defense_ids: list[str] = Field(default_factory=list)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
    provenance: str = "sample"


class CampaignResponse(StrictBaseModel):
    """Full campaign representation returned by the API."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    created_at: datetime
    status: str
    goals: list[str]
    categories: list[str]
    budget_per_goal: int
    defense_ids: list[str]
    config_snapshot: dict[str, Any]
    provenance: str = "sample"



# ───────────────────────────────────────────────────────────────
# TraceStep
# ───────────────────────────────────────────────────────────────
class TraceStepResponse(StrictBaseModel):
    """A single trace step in a conversation."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

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
class AttackSummaryResponse(StrictBaseModel):
    """Lightweight attack record for list views."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

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


class AttackResponse(StrictBaseModel):
    """Full attack record including trace steps and oracle verdict."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

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
class ReplayRequest(StrictBaseModel):
    """Request to statistically replay an attack."""

    attack_id: str
    n_runs: int = 10
    defense_ids: list[str] = Field(default_factory=list)


class ReplayResponse(StrictBaseModel):
    """Statistical replay results."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

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
class DefenseInfo(StrictBaseModel):
    """Descriptor for a single defense layer."""

    id: str
    name: str
    description: str = ""
    enabled: bool = True


class DefenseEvalRequest(StrictBaseModel):
    """Request to evaluate a set of defenses against a campaign."""

    campaign_id: str
    defense_combos: list[list[str]]


class EvalMatrixRequest(StrictBaseModel):
    """Request for a full evaluation matrix."""

    campaign_id: str
    defense_combos: list[list[str]]
    include_benign: bool = True


class EvalMatrixResponse(StrictBaseModel):
    """One row of the defense evaluation matrix."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

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
class MetricsSummaryResponse(StrictBaseModel):
    """Aggregated metrics for a campaign."""

    campaign_id: str
    provenance: str = "sample"  # real | sample
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
class AttackGraphNode(StrictBaseModel):
    """A node in the attack-trace graph."""

    id: str
    type: str
    label: str
    data: dict[str, Any] = Field(default_factory=dict)
    # data typically contains: content, tool_name, tool_args,
    # is_malicious, step_index


class AttackGraphEdge(StrictBaseModel):
    """An edge in the attack-trace graph."""

    id: str
    source: str
    target: str
    is_malicious_path: bool = False
    label: str = ""


class AttackGraphResponse(StrictBaseModel):
    """Full attack-trace graph for visualisation."""

    nodes: list[AttackGraphNode] = Field(default_factory=list)
    edges: list[AttackGraphEdge] = Field(default_factory=list)


# ───────────────────────────────────────────────────────────────
# SSE event schemas
# ───────────────────────────────────────────────────────────────
class AttackStartedEvent(StrictBaseModel):
    """Emitted when a new attack attempt begins."""

    event: str = "attack_started"
    attack_id: str
    campaign_id: str
    goal: str
    strategy: str
    iteration: int


class StepEvent(StrictBaseModel):
    """Emitted for each conversation step (message sent/received)."""

    event: str = "step"
    attack_id: str
    step_index: int
    role: str
    content: str


class ToolCallEvent(StrictBaseModel):
    """Emitted when the victim agent calls a tool."""

    event: str = "tool_call"
    attack_id: str
    step_index: int
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    tool_result: dict[str, Any] | None = None
    is_malicious: bool = False


class OracleVerdictEvent(StrictBaseModel):
    """Emitted when the oracle returns a judgement."""

    event: str = "oracle_verdict"
    attack_id: str
    verdict: OracleVerdict


class IterationScoreEvent(StrictBaseModel):
    """Emitted after each iteration is scored."""

    event: str = "iteration_score"
    attack_id: str
    iteration: int
    partial_score: float
    best_in_chain: bool


class AttackFinishedEvent(StrictBaseModel):
    """Emitted when an attack attempt ends."""

    event: str = "attack_finished"
    attack_id: str
    status: str
    partial_score: float
    oracle_verdict: OracleVerdict | None = None
