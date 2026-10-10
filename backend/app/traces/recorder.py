"""
Trace recorder — captures every step of an agent run.

Each step is a timestamped event (message, tool call, or verdict).
Implements Domain 10 Hash Chaining over prev_hash and canonical JSON payloads,
persisting Events, TraceSteps, and RunSeals to the database.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.oracle.oracle import OracleVerdict
from app.traces.hash_chain import compute_event_hash, generate_run_seal


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
    """Captures every step of a single agent run with hash-chain integrity.

    Parameters
    ----------
    attack_id:
        Unique identifier for the attack run this trace belongs to.
    """

    def __init__(self, attack_id: str, run_id: str | None = None) -> None:
        self.attack_id = attack_id
        self.run_id = run_id or attack_id
        self._steps: list[TraceStep] = []
        self._verdict: OracleVerdict | None = None
        self._head_hash: str = "0" * 64

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
        """Build a React Flow–compatible graph from recorded steps."""
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        malicious_node_ids: set[str] = set()

        for step in self._steps:
            if step.kind == "verdict":
                continue

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

    # ── persistence & hash chain ───────────────────────────────────

    async def save_to_db(self, session: Any) -> None:
        """Persist every TraceStep and Event with SHA256 hash chaining."""
        from app.models import TraceStep as TraceStepRow, Event, RunSeal, Run
        from app.config import get_settings

        # Check or create Run record
        run_obj = await session.get(Run, self.run_id)
        if not run_obj:
            run_obj = Run(id=self.run_id, attack_id=self.attack_id)
            session.add(run_obj)
            await session.flush()

        prev_hash = "0" * 64

        for seq, step in enumerate(self._steps):
            payload = step.to_dict()
            curr_hash = compute_event_hash(prev_hash, payload)

            # Insert append-only Event
            event_row = Event(
                run_id=self.run_id,
                seq=seq,
                event_type=step.kind,
                actor="victim" if step.role != "user" else "attacker",
                payload=payload,
                prev_hash=prev_hash,
                hash=curr_hash,
            )
            session.add(event_row)

            # Insert legacy TraceStep for backwards compatibility
            step_row = TraceStepRow(
                attack_id=self.attack_id,
                step_index=step.step_index,
                role=step.role or "system",
                content=step.content or json.dumps(payload),
                tool_name=step.tool_name,
                tool_args=step.tool_args,
                tool_result=step.tool_result if isinstance(step.tool_result, (dict, list)) else {"raw": str(step.tool_result)},
                is_malicious=step.is_malicious,
            )
            session.add(step_row)

            prev_hash = curr_hash

        self._head_hash = prev_hash
        run_obj.head_hash = self._head_hash
        run_obj.tool_call_count = len([s for s in self._steps if s.kind == "tool_call"])

        # Create RunSeal
        seal_secret = get_settings().trace_seal_key
        seal_hmac = generate_run_seal(self.run_id, self._head_hash, len(self._steps), seal_secret)

        seal_row = RunSeal(
            run_id=self.run_id,
            head_hash=self._head_hash,
            event_count=len(self._steps),
            seal_hmac=seal_hmac,
        )
        session.add(seal_row)
        await session.flush()

    # ── serialisation ─────────────────────────────────────────────

    def to_json(self) -> str:
        """Serialise the full trace (steps + verdict) as a JSON string."""
        payload: dict[str, Any] = {
            "attack_id": self.attack_id,
            "run_id": self.run_id,
            "steps": self.get_trace_steps(),
            "head_hash": self._head_hash,
        }
        if self._verdict is not None:
            payload["verdict"] = asdict(self._verdict)
        return json.dumps(payload, default=str)

    @classmethod
    def from_json(cls, data: str) -> TraceRecorder:
        """Deserialise a JSON string into a TraceRecorder."""
        payload = json.loads(data)
        recorder = cls(attack_id=payload["attack_id"], run_id=payload.get("run_id"))

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
        return "llm_decision"

    if step.kind == "tool_call":
        tool = step.tool_name or ""
        from app.victim.fake_data import CANARY_STRINGS, CANARY_SECRETS

        result_lower = str(step.tool_result).lower()
        for canary in list(CANARY_STRINGS) + list(CANARY_SECRETS):
            if canary.lower() in result_lower:
                return "leak"

        if tool in ("search_docs", "read_email"):
            return "retrieved_doc"
        return "tool_call"

    return "tool_call"


def _node_label(step: TraceStep) -> str:
    """Generate a human-readable label for a graph node."""
    if step.kind == "message":
        preview = (step.content or "")[:60]
        return f"[{step.role}] {preview}{'…' if len(step.content or '') > 60 else ''}"

    if step.kind == "tool_call":
        return f"{step.tool_name}()"

    return step.kind
