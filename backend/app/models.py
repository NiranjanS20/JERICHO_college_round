"""
SQLAlchemy ORM models for AgentBreak.

Every table uses string UUIDs as primary keys and stores complex data
(lists, dicts) in JSON columns for maximum flexibility with SQLite.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


def _uuid() -> str:
    """Generate a new UUID4 string for use as a default PK."""
    return str(uuid.uuid4())


# ── Campaign ────────────────────────────────────────────────────
class Campaign(Base):
    """A red-team campaign — a batch of attacks against one or more goals."""

    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=_uuid
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    status: Mapped[str] = mapped_column(
        String, default="pending"
    )  # pending | running | completed | failed
    user_id: Mapped[str] = mapped_column(String, default="default-user")
    workspace_id: Mapped[str] = mapped_column(String, default="default-workspace")
    provenance: Mapped[str] = mapped_column(String, default="sample")  # real | sample
    goals: Mapped[list] = mapped_column(JSON, default=list)
    categories: Mapped[list] = mapped_column(JSON, default=list)
    budget_per_goal: Mapped[int] = mapped_column(Integer, default=10)
    defense_ids: Mapped[list] = mapped_column(JSON, default=list)
    config_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    attacks: Mapped[list[Attack]] = relationship(
        "Attack", back_populates="campaign", cascade="all, delete-orphan"
    )
    eval_matrix_results: Mapped[list[EvalMatrixResult]] = relationship(
        "EvalMatrixResult", back_populates="campaign", cascade="all, delete-orphan"
    )


# ── Attack ──────────────────────────────────────────────────────
class Attack(Base):
    """A single attack attempt within a campaign."""

    __tablename__ = "attacks"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=_uuid
    )
    campaign_id: Mapped[str] = mapped_column(
        String, ForeignKey("campaigns.id"), nullable=False
    )
    goal: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    strategy: Mapped[str] = mapped_column(String, nullable=False)
    iteration: Mapped[int] = mapped_column(Integer, nullable=False)
    injection_point: Mapped[str] = mapped_column(
        String, nullable=False
    )  # direct | doc:<id> | email:<id> | memory
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String, default="running"
    )  # running | success | failure | error
    oracle_verdict: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    partial_score: Mapped[float] = mapped_column(Float, default=0.0)
    best_in_chain: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    campaign: Mapped[Campaign] = relationship(
        "Campaign", back_populates="attacks"
    )
    trace_steps: Mapped[list[TraceStep]] = relationship(
        "TraceStep", back_populates="attack", cascade="all, delete-orphan"
    )
    replay_results: Mapped[list[ReplayResult]] = relationship(
        "ReplayResult", back_populates="attack", cascade="all, delete-orphan"
    )


# ── TraceStep ───────────────────────────────────────────────────
class TraceStep(Base):
    """One step in a conversation trace — a message, tool call, or tool result."""

    __tablename__ = "trace_steps"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=_uuid
    )
    attack_id: Mapped[str] = mapped_column(
        String, ForeignKey("attacks.id"), nullable=False
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(
        String, nullable=False
    )  # system | user | assistant | tool_call | tool_result
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_args: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tool_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_malicious: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    attack: Mapped[Attack] = relationship(
        "Attack", back_populates="trace_steps"
    )


# ── ReplayResult ────────────────────────────────────────────────
class ReplayResult(Base):
    """Statistical replay result for a single attack."""

    __tablename__ = "replay_results"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=_uuid
    )
    attack_id: Mapped[str] = mapped_column(
        String, ForeignKey("attacks.id"), nullable=False
    )
    n_runs: Mapped[int] = mapped_column(Integer, nullable=False)
    successes: Mapped[int] = mapped_column(Integer, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    wilson_ci_low: Mapped[float] = mapped_column(Float, nullable=False)
    wilson_ci_high: Mapped[float] = mapped_column(Float, nullable=False)
    defenses_used: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    attack: Mapped[Attack] = relationship(
        "Attack", back_populates="replay_results"
    )


# ── EvalMatrixResult ────────────────────────────────────────────
class EvalMatrixResult(Base):
    """Defense evaluation matrix row — one row per defense combo per campaign."""

    __tablename__ = "eval_matrix_results"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=_uuid
    )
    campaign_id: Mapped[str] = mapped_column(
        String, ForeignKey("campaigns.id"), nullable=False
    )
    defense_combo: Mapped[list] = mapped_column(JSON, default=list)
    attack_success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    benign_pass_rate: Mapped[float] = mapped_column(Float, nullable=False)
    regressions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    adaptive_asr: Mapped[float] = mapped_column(Float, nullable=False)
    static_asr: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    campaign: Mapped[Campaign] = relationship(
        "Campaign", back_populates="eval_matrix_results"
    )
