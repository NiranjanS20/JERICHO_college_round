"""
Trace recorder — captures every step of an agent run.

Each step is a timestamped event (message, tool call, or verdict).
The recorder can build a React Flow–compatible attack graph for
visualising the attack chain in the frontend.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.oracle.oracle import OracleVerdict


# ---------------------------------------------------------------------------
# Trace step data
# ---------------------------------------------------------------------------

@dataclass
class TraceStep:
    """Single atomic event in an attack trace."""

    step_index: int
    timestamp: str
    kind: str  # "message" | "tool_call" | "verdict"
    role: str | None = None           # for messages
    content: str | None = None        # for messages
    tool_name: str | None = None      # for tool calls
    tool_args: dict[str, Any] | None = None
    tool_result: Any = None
    is_malicious: bool = False
    verdict: dict[str, Any] | None = None  # for verdict step

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


# ---------------------------------------------------------------------------
# Graph node / edge
# ---------------------------------------------------------------------------

@dataclass
class GraphNode:
    """React Flow node."""

    id: str
    type: str  # user_input | retrieved_doc | llm_decision | tool_call | leak
    label: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise for the React Flow ``nodes`` array."""
        return {
            "id": self.id,
            "type": self.type,
            "data": {"label": self.label, **self.data},
            "position": {"x": 0, "y": 0},  # layout handled by frontend
        }


@dataclass
class GraphEdge:
    """React Flow edge."""

    id: str
    source: str
    target: str
    is_malicious_path: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialise for the React Flow ``edges`` array."""
        d: dict[str, Any] = {
            "id": self.id,
            "source": self.source,
            "target": self.target,
        }
        if self.is_malicious_path:
            d["style"] = {"stroke": "#ff4444", "strokeWidth": 2}
            d["animated"] = True
            d["data"] = {"is_malicious_path": True}
        return d


# ---------------------------------------------------------------------------
# Recorder
# ---------------------------------------------------------------------------

class TraceRecorder:
    """Captures every step of a single agent run.

    Parameters
    ----------
    attack_id:
        Unique identifier for the attack run this trace belongs to.
    """

    def __init__(self, attack_id: str) -> None:
        self.attack_id = attack_id
        self._steps: list[TraceStep] = []
        self._verdict: OracleVerdict | None = None

    # ── recording API ─────────────────────────────────────────────

    def record_message(
        self,
        role: str,
        content: str,
        step_index: int,
    ) -> None:
        """Record a conversation message (user / assistant / system)."""
        self._steps.append(
            TraceStep(
                step_index=step_index,
                timestamp=_now_iso(),
                kind="message",
                role=role,
                content=content,
            )
        )

    def record_tool_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: Any,
        step_index: int,
        is_malicious: bool = False,
    ) -> None:
        """Record a single tool invocation and its result."""
        self._steps.append(
            TraceStep(
                step_index=step_index,
                timestamp=_now_iso(),
                kind="tool_call",
                tool_name=tool_name,
                tool_args=args,
                tool_result=result,
                is_malicious=is_malicious,
            )
        )

    def record_verdict(self, verdict: OracleVerdict) -> None:
        """Attach the oracle verdict to the trace."""
        self._verdict = verdict
        self._steps.append(
            TraceStep(
                step_index=len(self._steps),
                timestamp=_now_iso(),
                kind="verdict",
                verdict=asdict(verdict),
            )
        )

    # ── query API ─────────────────────────────────────────────────

    def get_trace_steps(self) -> list[dict[str, Any]]:
        """Return all recorded steps as plain dicts."""
        return [s.to_dict() for s in self._steps]

    # ── attack graph ──────────────────────────────────────────────

    def build_attack_graph(self) -> dict[str, Any]:
        """Build a React Flow–compatible graph from recorded steps.

        Returns
        -------
        dict
            ``{"nodes": [...], "edges": [...]}`` ready for the frontend.
        """
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        malicious_node_ids: set[str] = set()

        for step in self._steps:
            if step.kind == "verdict":
                continue  # verdict is metadata, not a graph node

            node_id = f"step-{step.step_index}"
            node_type = _classify_node(step)
            label = _node_label(step)

            node = GraphNode(
                id=node_id,
                type=node_type,
                label=label,
                data={"step_index": step.step_index, "kind": step.kind},
            )
            nodes.append(node)

            if node_type == "leak" or step.is_malicious:
                malicious_node_ids.add(node_id)

        # Edges: connect sequential non-verdict steps
        non_verdict = [n for n in nodes]
        for i in range(1, len(non_verdict)):
            src = non_verdict[i - 1]
            tgt = non_verdict[i]
            is_mal = src.id in malicious_node_ids or tgt.id in malicious_node_ids
            edges.append(
                GraphEdge(
                    id=f"e-{src.id}-{tgt.id}",
                    source=src.id,
                    target=tgt.id,
                    is_malicious_path=is_mal,
                )
            )

        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
        }

    # ── persistence ───────────────────────────────────────────────

    async def save_to_db(self, session: Any) -> None:
        """Persist every :class:`TraceStep` to the database.

        Parameters
        ----------
        session:
            An ``AsyncSession`` (SQLAlchemy). The import of the ORM model
            is deferred so this module doesn't force a hard dependency on
            the DB layer at import time.
        """
        # Lazy import to avoid circular / missing-module errors at import time
        from app.models import TraceStepRow  # type: ignore[import-untyped]

        for step in self._steps:
            row = TraceStepRow(
                attack_id=self.attack_id,
                step_index=step.step_index,
                kind=step.kind,
                data=json.dumps(step.to_dict()),
            )
            session.add(row)
        await session.flush()

    # ── serialisation ─────────────────────────────────────────────

    def to_json(self) -> str:
        """Serialise the full trace (steps + verdict) as a JSON string."""
        payload: dict[str, Any] = {
            "attack_id": self.attack_id,
            "steps": self.get_trace_steps(),
        }
        if self._verdict is not None:
            payload["verdict"] = asdict(self._verdict)
        return json.dumps(payload, default=str)

    @classmethod
    def from_json(cls, data: str) -> TraceRecorder:
        """Deserialise a JSON string into a :class:`TraceRecorder`.

        Parameters
        ----------
        data:
            JSON string previously produced by :meth:`to_json`.
        """
        payload = json.loads(data)
        recorder = cls(attack_id=payload["attack_id"])

        for raw_step in payload.get("steps", []):
            step = TraceStep(
                step_index=raw_step.get("step_index", 0),
                timestamp=raw_step.get("timestamp", _now_iso()),
                kind=raw_step.get("kind", "message"),
                role=raw_step.get("role"),
                content=raw_step.get("content"),
                tool_name=raw_step.get("tool_name"),
                tool_args=raw_step.get("tool_args"),
                tool_result=raw_step.get("tool_result"),
                is_malicious=raw_step.get("is_malicious", False),
                verdict=raw_step.get("verdict"),
            )
            recorder._steps.append(step)

        if "verdict" in payload:
            v = payload["verdict"]
            recorder._verdict = OracleVerdict(**v)

        return recorder


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _classify_node(step: TraceStep) -> str:
    """Map a trace step to a React Flow node type."""
    if step.is_malicious:
        return "leak"

    if step.kind == "message":
        if step.role == "user":
            return "user_input"
        return "llm_decision"  # assistant or system

    if step.kind == "tool_call":
        tool = step.tool_name or ""
        # Detect canary in the tool result to mark as leak
        from app.victim.fake_data import CANARY_STRINGS, CANARY_SECRETS

        result_lower = str(step.tool_result).lower()
        for canary in list(CANARY_STRINGS) + list(CANARY_SECRETS):
            if canary.lower() in result_lower:
                return "leak"

        if tool in ("search_docs", "read_email"):
            return "retrieved_doc"
        return "tool_call"

    return "tool_call"  # fallback


def _node_label(step: TraceStep) -> str:
    """Generate a human-readable label for a graph node."""
    if step.kind == "message":
        preview = (step.content or "")[:60]
        return f"[{step.role}] {preview}{'…' if len(step.content or '') > 60 else ''}"

    if step.kind == "tool_call":
        return f"{step.tool_name}()"

    return step.kind
