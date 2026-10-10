"""
SQLAlchemy ORM models for AgentBreak.

Fully implements the ab schema tables for both Supabase PostgreSQL
and local SQLite fallback environments.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


def _uuid() -> str:
    """Generate a new UUID4 string for use as a default PK."""
    return str(uuid.uuid4())


# ── Profiles ────────────────────────────────────────────────────
class Profile(Base):
    """Platform user profile."""

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="viewer") # admin | security_engineer | viewer
    status: Mapped[str] = mapped_column(String, default="active") # active | disabled
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


# ── Targets & Target Versions ──────────────────────────────────
class Target(Base):
    """Target victim application under evaluation."""

    __tablename__ = "targets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    preset_key: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    current_version_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, ForeignKey("profiles.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TargetVersion(Base):
    """Immutable version configuration of a Target."""

    __tablename__ = "target_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    target_id: Mapped[str] = mapped_column(String, ForeignKey("targets.id"), nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    manifest: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RAGSource(Base):
    """RAG document collection for a target version."""

    __tablename__ = "rag_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    target_version_id: Mapped[str] = mapped_column(String, ForeignKey("target_versions.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    trust: Mapped[str] = mapped_column(String, default="untrusted") # trusted | untrusted
    docs: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── Fixtures & Canaries ─────────────────────────────────────────
class Fixture(Base):
    """Synthetic sandbox data fixture."""

    __tablename__ = "fixtures"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    seed: Mapped[int] = mapped_column(Integer, nullable=False, default=42)
    version: Mapped[str] = mapped_column(String, nullable=False, default="1.0.0")
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Canary(Base):
    """Canary secret token generated per fixture."""

    __tablename__ = "canaries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    fixture_id: Mapped[str] = mapped_column(String, ForeignKey("fixtures.id"), nullable=False)
    record_ref: Mapped[str] = mapped_column(String, nullable=False)
    sensitivity: Mapped[str] = mapped_column(String, default="high")
    token_hmac: Mapped[str] = mapped_column(String, nullable=False)
    canary_token: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── Defenses & Defense Versions ─────────────────────────────────
class DefenseProfile(Base):
    """Named set of security controls."""

    __tablename__ = "defense_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    current_version_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DefenseProfileVersion(Base):
    """Immutable version configuration of a Defense Profile."""

    __tablename__ = "defense_profile_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    defense_profile_id: Mapped[str] = mapped_column(String, ForeignKey("defense_profiles.id"), nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    controls: Mapped[dict] = mapped_column(JSON, default=dict)
    determinism: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    parent_version_id: Mapped[str | None] = mapped_column(String, ForeignKey("defense_profile_versions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── Campaign ────────────────────────────────────────────────────
class Campaign(Base):
    """A red-team evaluation campaign."""

    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    target_version_id: Mapped[str | None] = mapped_column(String, ForeignKey("target_versions.id"), nullable=True)
    defense_profile_version_id: Mapped[str | None] = mapped_column(String, ForeignKey("defense_profile_versions.id"), nullable=True)
    mode: Mapped[str] = mapped_column(String, default="black") # white | black
    surfaces: Mapped[list] = mapped_column(JSON, default=list) # instructions | memory | retrieval | tool_permissions | multi_step
    goals: Mapped[list] = mapped_column(JSON, default=list)
    categories: Mapped[list] = mapped_column(JSON, default=list)
    budget_per_goal: Mapped[int] = mapped_column(Integer, default=10)
    status: Mapped[str] = mapped_column(String, default="pending") # pending | running | completed | failed | cancelled | interrupted
    budget: Mapped[dict] = mapped_column(JSON, default=dict)
    llm_calls_used: Mapped[int] = mapped_column(Integer, default=0)
    attempts_used: Mapped[int] = mapped_column(Integer, default=0)
    config_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    defense_ids: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, ForeignKey("profiles.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    attacks: Mapped[list[Attack]] = relationship("Attack", back_populates="campaign", cascade="all, delete-orphan")
    eval_matrix_results: Mapped[list[EvalMatrixResult]] = relationship("EvalMatrixResult", back_populates="campaign", cascade="all, delete-orphan")


# ── Attack ──────────────────────────────────────────────────────
class Attack(Base):
    """A single attack attempt within a campaign."""

    __tablename__ = "attacks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, ForeignKey("campaigns.id"), nullable=False)
    iteration: Mapped[int] = mapped_column(Integer, nullable=False)
    beam_depth: Mapped[int] = mapped_column(Integer, default=1)
    parent_attack_id: Mapped[str | None] = mapped_column(String, ForeignKey("attacks.id"), nullable=True)
    goal: Mapped[str] = mapped_column(String, nullable=False)
    surface: Mapped[str] = mapped_column(String, default="instructions")
    category: Mapped[str] = mapped_column(String, nullable=False)
    strategy: Mapped[str] = mapped_column(String, nullable=False)
    injection_point: Mapped[str] = mapped_column(String, default="direct")
    payload: Mapped[dict | str] = mapped_column(JSON, nullable=False)
    verdict: Mapped[str] = mapped_column(String, default="error") # refused | denied | partial | success | error
    status: Mapped[str] = mapped_column(String, default="running")
    partial_score: Mapped[float] = mapped_column(Float, default=0.0)
    model_assisted: Mapped[bool] = mapped_column(Boolean, default=False)
    best_in_chain: Mapped[bool] = mapped_column(Boolean, default=False)
    oracle_verdict: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    campaign: Mapped[Campaign] = relationship("Campaign", back_populates="attacks")
    trace_steps: Mapped[list[TraceStep]] = relationship("TraceStep", back_populates="attack", cascade="all, delete-orphan")
    runs: Mapped[list[Run]] = relationship("Run", back_populates="attack", cascade="all, delete-orphan")
    replay_results: Mapped[list[ReplayResult]] = relationship("ReplayResult", back_populates="attack", cascade="all, delete-orphan")


# ── Runs, Events & Integrity ───────────────────────────────────
class Run(Base):
    """An execution run of an attack or benign task."""

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    attack_id: Mapped[str | None] = mapped_column(String, ForeignKey("attacks.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String, default="live") # live | replay | rerun | validation | regression
    target_version_id: Mapped[str | None] = mapped_column(String, ForeignKey("target_versions.id"), nullable=True)
    defense_profile_version_id: Mapped[str | None] = mapped_column(String, ForeignKey("defense_profile_versions.id"), nullable=True)
    fixture_id: Mapped[str | None] = mapped_column(String, ForeignKey("fixtures.id"), nullable=True)
    seed: Mapped[int] = mapped_column(Integer, default=42)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0)
    llm_calls: Mapped[int] = mapped_column(Integer, default=0)
    head_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    attack: Mapped[Attack | None] = relationship("Attack", back_populates="runs")
    events: Mapped[list[Event]] = relationship("Event", back_populates="run", cascade="all, delete-orphan")


class Event(Base):
    """Append-only tamper-evident event in an execution run."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("runs.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str] = mapped_column(String, default="victim")
    taint: Mapped[list] = mapped_column(JSON, default=list)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    parent_seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prev_hash: Mapped[str] = mapped_column(String, nullable=False)
    hash: Mapped[str] = mapped_column(String, nullable=False)

    run: Mapped[Run] = relationship("Run", back_populates="events")

    __table_args__ = (
        UniqueConstraint("run_id", "seq", name="uq_events_run_seq"),
    )


class RunSeal(Base):
    """HMAC seal for a completed run."""

    __tablename__ = "run_seals"

    run_id: Mapped[str] = mapped_column(String, ForeignKey("runs.id"), primary_key=True)
    head_hash: Mapped[str] = mapped_column(String, nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False)
    seal_hmac: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ModelCall(Base):
    """Recorded LLM invocation for audit & exact replay."""

    __tablename__ = "model_calls"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    run_id: Mapped[str | None] = mapped_column(String, ForeignKey("runs.id"), nullable=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String, nullable=False)
    prompt: Mapped[dict] = mapped_column(JSON, nullable=False)
    response: Mapped[dict] = mapped_column(JSON, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.0)
    from_cache: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LLMCache(Base):
    """Prompt-hash cache for LLM responses."""

    __tablename__ = "llm_cache"

    prompt_hash: Mapped[str] = mapped_column(String, primary_key=True)
    model: Mapped[str] = mapped_column(String, nullable=False)
    response: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── TraceStep (Backwards Compatibility UI Model) ───────────────
class TraceStep(Base):
    """Legacy trace step representation for UI rendering."""

    __tablename__ = "trace_steps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    attack_id: Mapped[str] = mapped_column(String, ForeignKey("attacks.id"), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_args: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tool_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_malicious: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    attack: Mapped[Attack] = relationship("Attack", back_populates="trace_steps")


# ── Findings & Evidence ────────────────────────────────────────
class Finding(Base):
    """Vulnerability finding discovered during red-team evaluation."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    target_version_id: Mapped[str] = mapped_column(String, ForeignKey("target_versions.id"), nullable=False)
    root_cause_key: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    surface: Mapped[str] = mapped_column(String, nullable=False)
    root_cause: Mapped[str] = mapped_column(String, nullable=False)
    impact: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    exploitability: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    reach: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    severity_score: Mapped[int] = mapped_column(Integer, default=27)
    severity: Mapped[str] = mapped_column(String, default="Medium") # Low | Medium | High | Critical
    owasp_id: Mapped[str] = mapped_column(String, nullable=False, default="LLM01:2025")
    atlas_id: Mapped[str | None] = mapped_column(String, nullable=True)
    reliability_k: Mapped[int] = mapped_column(Integer, default=1)
    reliability_n: Mapped[int] = mapped_column(Integer, default=1)
    ci_low: Mapped[float] = mapped_column(Float, default=0.0)
    ci_high: Mapped[float] = mapped_column(Float, default=1.0)
    flaky: Mapped[bool] = mapped_column(Boolean, default=False)
    model_assisted: Mapped[bool] = mapped_column(Boolean, default=False)
    breaking_event_seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, default="open") # open | mitigated | fixed | regressed
    minimized_exploit: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    nist_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("target_version_id", "root_cause_key", name="uq_findings_target_root_cause"),
    )


class FindingEvidence(Base):
    """Link between a finding, run, and specific breaking event sequence."""

    __tablename__ = "finding_evidence"

    finding_id: Mapped[str] = mapped_column(String, ForeignKey("findings.id"), primary_key=True)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("runs.id"), primary_key=True)
    event_seq: Mapped[int] = mapped_column(Integer, primary_key=True)


class AttackCorpus(Base):
    """Regression corpus entry for a discovered finding."""

    __tablename__ = "attack_corpus"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    finding_id: Mapped[str] = mapped_column(String, ForeignKey("findings.id"), nullable=False)
    minimized_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AuditFinding(Base):
    """Permission Auditor finding (static tool vs manifest gap)."""

    __tablename__ = "audit_findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    target_version_id: Mapped[str] = mapped_column(String, ForeignKey("target_versions.id"), nullable=False)
    tool: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    granted_scope: Mapped[str] = mapped_column(String, nullable=False)
    intended_scope: Mapped[str] = mapped_column(String, nullable=False)
    gap: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, default="Medium")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── Defense Evaluation Models ───────────────────────────────────
class BenignTask(Base):
    """Benign employee workflow task for utility retention testing."""

    __tablename__ = "benign_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    expected_state: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ValidationResult(Base):
    """Result of validation Checks A, B, C against a defense version."""

    __tablename__ = "validation_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    finding_id: Mapped[str] = mapped_column(String, ForeignKey("findings.id"), nullable=False)
    defense_profile_version_id: Mapped[str] = mapped_column(String, ForeignKey("defense_profile_versions.id"), nullable=False)
    check_a: Mapped[dict] = mapped_column(JSON, default=dict)
    check_b: Mapped[dict] = mapped_column(JSON, default=dict)
    check_c: Mapped[dict] = mapped_column(JSON, default=dict)
    verdict: Mapped[str] = mapped_column(String, default="not_fixed") # fixed | partially_mitigated | not_fixed | fixed_with_regression
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class EvalResult(Base):
    """Defense evaluation matrix result for a specific defense combination."""

    __tablename__ = "eval_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str | None] = mapped_column(String, ForeignKey("campaigns.id"), nullable=True)
    combo_bits: Mapped[int] = mapped_column(Integer, default=0)
    defense_combo: Mapped[list] = mapped_column(JSON, default=list)
    asr_k: Mapped[int] = mapped_column(Integer, default=0)
    asr_n: Mapped[int] = mapped_column(Integer, default=0)
    benign_pass: Mapped[int] = mapped_column(Integer, default=0)
    benign_total: Mapped[int] = mapped_column(Integer, default=0)
    utility_retention: Mapped[float] = mapped_column(Float, default=1.0)
    regressions: Mapped[list] = mapped_column(JSON, default=list)
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class EvalMatrixResult(Base):
    """Backwards compatibility model for EvalMatrixResult."""

    __tablename__ = "eval_matrix_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, ForeignKey("campaigns.id"), nullable=False)
    defense_combo: Mapped[list] = mapped_column(JSON, default=list)
    attack_success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    benign_pass_rate: Mapped[float] = mapped_column(Float, nullable=False)
    regressions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    adaptive_asr: Mapped[float] = mapped_column(Float, nullable=False)
    static_asr: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    campaign: Mapped[Campaign] = relationship("Campaign", back_populates="eval_matrix_results")


class RegressionRun(Base):
    """Regression test suite run."""

    __tablename__ = "regression_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    defense_profile_version_id: Mapped[str] = mapped_column(String, ForeignKey("defense_profile_versions.id"), nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ── Governance & Approvals ──────────────────────────────────────
class Approval(Base):
    """Human approval gate request."""

    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("runs.id"), nullable=False)
    event_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    tool: Mapped[str] = mapped_column(String, nullable=False)
    args: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="pending") # pending | approved | denied | expired
    decided_by: Mapped[str | None] = mapped_column(String, ForeignKey("profiles.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Report(Base):
    """Generated PDF/HTML export report metadata."""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    format: Mapped[str] = mapped_column(String, nullable=False) # json | html | pdf
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    sha256: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String, ForeignKey("profiles.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AuditLog(Base):
    """Append-only platform security audit log."""

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    actor: Mapped[str | None] = mapped_column(String, ForeignKey("profiles.id"), nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    entity: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    ip: Mapped[str | None] = mapped_column(String, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── Replay Result Model (Legacy UI Compatible) ──────────────────
class ReplayResult(Base):
    """Statistical replay result."""

    __tablename__ = "replay_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    attack_id: Mapped[str] = mapped_column(String, ForeignKey("attacks.id"), nullable=False)
    n_runs: Mapped[int] = mapped_column(Integer, nullable=False)
    successes: Mapped[int] = mapped_column(Integer, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    wilson_ci_low: Mapped[float] = mapped_column(Float, nullable=False)
    wilson_ci_high: Mapped[float] = mapped_column(Float, nullable=False)
    defenses_used: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    attack: Mapped[Attack] = relationship("Attack", back_populates="replay_results")


# ── Standards Lookup Models ────────────────────────────────────
class OwaspCategory(Base):
    """OWASP Top 10 for LLM Applications reference entry."""

    __tablename__ = "owasp_llm_categories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class AtlasTechnique(Base):
    """MITRE ATLAS reference entry."""

    __tablename__ = "atlas_techniques"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class RootCauseMap(Base):
    """Mapping from root cause key to OWASP and ATLAS standards."""

    __tablename__ = "root_cause_map"

    root_cause_key: Mapped[str] = mapped_column(String, primary_key=True)
    owasp_id: Mapped[str] = mapped_column(String, ForeignKey("owasp_llm_categories.id"), nullable=False)
    atlas_id: Mapped[str | None] = mapped_column(String, ForeignKey("atlas_techniques.id"), nullable=True)
