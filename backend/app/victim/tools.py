"""
Mocked tool implementations for the Acme Corp victim agent.

Every tool call is recorded in ``_call_log`` so the oracle, evaluation
harness, and traces subsystem can inspect exactly what happened during
a run.  No tool has real side effects — emails are not sent, databases
are not modified.

The module also exposes a ``TOOL_REGISTRY`` (name → callable) and a
``get_tool_declarations()`` helper that returns Gemini-compatible
function declarations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from google.genai import types

from app.victim import fake_data
from app.victim.memory import MemoryStore

# ── Call logging ────────────────────────────────────────────────────


@dataclass
class ToolCallLog:
    """A single recorded tool invocation."""

    tool_name: str
    args: dict[str, Any]
    result: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


_call_log: list[ToolCallLog] = []


def get_call_log() -> list[ToolCallLog]:
    """Return the current call log (reference, not copy)."""
    return _call_log


def clear_call_log() -> None:
    """Reset the call log between runs."""
    _call_log.clear()


# ── Session context ─────────────────────────────────────────────────

_current_session_id: str | None = None


def set_session_id(session_id: str) -> None:
    """Set the session ID used by memory tools for the current run."""
    global _current_session_id
    _current_session_id = session_id


def _get_memory_store() -> MemoryStore:
    """Return the MemoryStore for the active session."""
    if _current_session_id is None:
        raise RuntimeError("No session_id set — call set_session_id() first")
    return MemoryStore.get_or_create(_current_session_id)


# ── Helper to log and return ────────────────────────────────────────


def _log(name: str, args: dict[str, Any], result: Any) -> Any:
    """Append to the call log and return *result* unchanged."""
    _call_log.append(ToolCallLog(tool_name=name, args=args, result=result))
    return result


# ── Tool implementations ───────────────────────────────────────────


async def read_email(email_id: str) -> dict[str, Any]:
    """Read a single email by its ID."""
    email = fake_data.get_email(email_id)
    if email is None:
        result: dict[str, Any] = {"error": f"Email {email_id!r} not found"}
    else:
        result = dict(email)
    return _log("read_email", {"email_id": email_id}, result)


async def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send an email (mocked — nothing is actually sent)."""
    result: dict[str, Any] = {"status": "sent", "to": to, "subject": subject}
    return _log("send_email", {"to": to, "subject": subject, "body": body}, result)


async def search_docs(query: str) -> list[dict[str, Any]]:
    """Search internal documents by keyword."""
    hits = fake_data.search_documents(query)
    result: list[dict[str, Any]] = [dict(d) for d in hits]
    return _log("search_docs", {"query": query}, result)


async def query_customer_db(query: str) -> list[dict[str, Any]]:
    """Search customer records by name or email (substring match)."""
    query_lower = query.lower()
    matches: list[dict[str, Any]] = [
        dict(c)
        for c in fake_data.CUSTOMERS
        if query_lower in str(c["name"]).lower()
        or query_lower in str(c["email"]).lower()
    ]
    return _log("query_customer_db", {"query": query}, matches)


async def write_memory(key: str, value: str) -> dict[str, str]:
    """Write a key-value pair to the session memory store."""
    store = _get_memory_store()
    await store.write(key, value)
    result: dict[str, str] = {"status": "written", "key": key}
    return _log("write_memory", {"key": key, "value": value}, result)


async def read_memory() -> dict[str, str]:
    """Read all entries from the session memory store."""
    store = _get_memory_store()
    data = await store.read_all()
    return _log("read_memory", {}, data)


# ── Registry ────────────────────────────────────────────────────────

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "read_email": read_email,
    "send_email": send_email,
    "search_docs": search_docs,
    "query_customer_db": query_customer_db,
    "write_memory": write_memory,
    "read_memory": read_memory,
}

# ── Gemini-compatible function declarations ─────────────────────────


def get_tool_declarations() -> list[types.Tool]:
    """Return Gemini-compatible tool declarations for all registered tools.

    These are passed directly to the ``tools`` parameter of
    ``generate_content``.
    """
    declarations = [
        types.FunctionDeclaration(
            name="read_email",
            description="Read a single email from the inbox by its ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "email_id": types.Schema(
                        type=types.Type.STRING,
                        description="The unique email identifier (e.g. 'EMAIL-001').",
                    ),
                },
                required=["email_id"],
            ),
        ),
        types.FunctionDeclaration(
            name="send_email",
            description="Send an email to the specified recipient.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "to": types.Schema(
                        type=types.Type.STRING,
                        description="Recipient email address.",
                    ),
                    "subject": types.Schema(
                        type=types.Type.STRING,
                        description="Email subject line.",
                    ),
                    "body": types.Schema(
                        type=types.Type.STRING,
                        description="Email body text.",
                    ),
                },
                required=["to", "subject", "body"],
            ),
        ),
        types.FunctionDeclaration(
            name="search_docs",
            description="Search internal documents by keyword query.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="Search keyword or phrase.",
                    ),
                },
                required=["query"],
            ),
        ),
        types.FunctionDeclaration(
            name="query_customer_db",
            description="Search the customer database by name or email.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="Search term to match against customer name or email.",
                    ),
                },
                required=["query"],
            ),
        ),
        types.FunctionDeclaration(
            name="write_memory",
            description="Store a key-value pair in the session memory for later recall.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "key": types.Schema(
                        type=types.Type.STRING,
                        description="Memory key to store the value under.",
                    ),
                    "value": types.Schema(
                        type=types.Type.STRING,
                        description="The value to store.",
                    ),
                },
                required=["key", "value"],
            ),
        ),
        types.FunctionDeclaration(
            name="read_memory",
            description="Read all stored key-value pairs from the session memory.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
    ]
    return [types.Tool(function_declarations=declarations)]
