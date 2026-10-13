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


# ── Sandbox Context & Execution Guard ──────────────────────────────
_is_sandbox_executing: bool = False


def set_sandbox_tool_executing(executing: bool) -> None:
    """Set the state indicating tool execution is currently active in the sandbox."""
    global _is_sandbox_executing
    _is_sandbox_executing = executing


def is_sandbox_tool_executing() -> bool:
    """Check if tool execution is currently active in the sandbox."""
    return _is_sandbox_executing



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


async def write_memory(key: str, value: str) -> dict[str, Any]:
    """Write a key-value pair to the session memory store."""
    store = _get_memory_store()
    write_result = await store.write(key, value)
    
    if write_result.get("error"):
        return _log("write_memory", {"key": key, "value": value}, write_result)
        
    result: dict[str, str] = {"status": "written", "key": key}
    return _log("write_memory", {"key": key, "value": value}, result)


async def read_memory() -> dict[str, Any]:
    """Read all entries from the session memory store."""
    store = _get_memory_store()
    data = await store.read_all()
    return _log("read_memory", {}, data)

# ── Support mock tools ────────────────────────────────────────────────
async def read_ticket(ticket_id: str) -> dict[str, Any]:
    ticket = fake_data.get_ticket(ticket_id)
    if not ticket:
        return _log("read_ticket", {"ticket_id": ticket_id}, {"error": "Ticket not found."})
    return _log("read_ticket", {"ticket_id": ticket_id}, ticket)

# ── HR mock tools ───────────────────────────────────────────────────
async def search_hr_policies(query: str) -> list[dict[str, Any]]:
    query_lower = query.lower()
    matches = [p for p in fake_data.HR_POLICIES if query_lower in p["title"].lower() or query_lower in p["content"].lower()]
    return _log("search_hr_policies", {"query": query}, matches)

async def get_employee_record(employee_id: str) -> dict[str, Any]:
    for emp in fake_data.HR_EMPLOYEES:
        if emp["id"] == employee_id:
            return _log("get_employee_record", {"employee_id": employee_id}, emp)
    return _log("get_employee_record", {"employee_id": employee_id}, {"error": "Employee not found."})

async def get_employee_leave_summary(employee_id: str) -> dict[str, Any]:
    for emp in fake_data.HR_EMPLOYEES:
        if emp["id"] == employee_id:
            return _log("get_employee_leave_summary", {"employee_id": employee_id}, {"leave_balance": emp["leave_balance"]})
    return _log("get_employee_leave_summary", {"employee_id": employee_id}, {"error": "Employee not found."})

# ── IT Ops mock tools ───────────────────────────────────────────────
async def get_incident(incident_id: str) -> dict[str, Any]:
    for inc in fake_data.IT_INCIDENTS:
        if inc["id"] == incident_id:
            return _log("get_incident", {"incident_id": incident_id}, inc)
    return _log("get_incident", {"incident_id": incident_id}, {"error": "Incident not found."})

async def search_asset_inventory(query: str) -> list[dict[str, Any]]:
    matches = [a for a in fake_data.IT_ASSETS if query.lower() in a["hostname"].lower()]
    return _log("search_asset_inventory", {"query": query}, matches)

async def get_service_health(service_id: str) -> dict[str, Any]:
    for svc in fake_data.IT_SERVICES:
        if svc["id"] == service_id:
            return _log("get_service_health", {"service_id": service_id}, svc)
    return _log("get_service_health", {"service_id": service_id}, {"error": "Service not found."})

async def restart_mock_service(service_id: str, approval_token: str = "") -> dict[str, Any]:
    if not approval_token or approval_token not in fake_data.IT_APPROVALS:
        return _log("restart_mock_service", {"service_id": service_id, "approval_token": approval_token}, {"error": "Unauthorized: Valid approval token required."})
    return _log("restart_mock_service", {"service_id": service_id, "approval_token": approval_token}, {"status": "success", "message": f"Service {service_id} restarted."})

async def change_mock_configuration(asset_id: str, new_config: str, approval_token: str = "") -> dict[str, Any]:
    if not approval_token or approval_token not in fake_data.IT_APPROVALS:
        return _log("change_mock_configuration", {"asset_id": asset_id, "new_config": new_config, "approval_token": approval_token}, {"error": "Unauthorized: Valid approval token required."})
    return _log("change_mock_configuration", {"asset_id": asset_id, "new_config": new_config, "approval_token": approval_token}, {"status": "success", "message": f"Config changed for {asset_id}."})


# ── Registry ────────────────────────────────────────────────────────

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "read_email": read_email,
    "send_email": send_email,
    "search_docs": search_docs,
    "query_customer_db": query_customer_db,
    "write_memory": write_memory,
    "read_memory": read_memory,
    "read_ticket": read_ticket,
    "search_hr_policies": search_hr_policies,
    "get_employee_record": get_employee_record,
    "get_employee_leave_summary": get_employee_leave_summary,
    "get_incident": get_incident,
    "search_asset_inventory": search_asset_inventory,
    "get_service_health": get_service_health,
    "restart_mock_service": restart_mock_service,
    "change_mock_configuration": change_mock_configuration,
}

# ── Gemini-compatible function declarations ─────────────────────────


def get_tool_declarations(allowed_tools: list[str] | set[str] | None = None) -> list[types.Tool]:
    """Return Gemini-compatible tool declarations, optionally filtered to allowed_tools."""
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
        types.FunctionDeclaration(
            name="read_ticket",
            description="Read a support ticket.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"ticket_id": types.Schema(type=types.Type.STRING)},
                required=["ticket_id"],
            )
        ),
        types.FunctionDeclaration(
            name="search_hr_policies",
            description="Search HR policies.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"query": types.Schema(type=types.Type.STRING)},
                required=["query"],
            )
        ),
        types.FunctionDeclaration(
            name="get_employee_record",
            description="Get employee record.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"employee_id": types.Schema(type=types.Type.STRING)},
                required=["employee_id"],
            )
        ),
        types.FunctionDeclaration(
            name="get_employee_leave_summary",
            description="Get employee leave summary.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"employee_id": types.Schema(type=types.Type.STRING)},
                required=["employee_id"],
            )
        ),
        types.FunctionDeclaration(
            name="get_incident",
            description="Get incident details.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"incident_id": types.Schema(type=types.Type.STRING)},
                required=["incident_id"],
            )
        ),
        types.FunctionDeclaration(
            name="search_asset_inventory",
            description="Search asset inventory.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"query": types.Schema(type=types.Type.STRING)},
                required=["query"],
            )
        ),
        types.FunctionDeclaration(
            name="get_service_health",
            description="Get service health.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"service_id": types.Schema(type=types.Type.STRING)},
                required=["service_id"],
            )
        ),
        types.FunctionDeclaration(
            name="restart_mock_service",
            description="Restart a service. Requires approval.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "service_id": types.Schema(type=types.Type.STRING),
                    "approval_token": types.Schema(type=types.Type.STRING),
                },
                required=["service_id"],
            )
        ),
        types.FunctionDeclaration(
            name="change_mock_configuration",
            description="Change service configuration. Requires approval.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "asset_id": types.Schema(type=types.Type.STRING),
                    "new_config": types.Schema(type=types.Type.STRING),
                    "approval_token": types.Schema(type=types.Type.STRING),
                },
                required=["asset_id", "new_config"],
            )
        ),
    ]
    if allowed_tools is not None:
        allowed_set = set(allowed_tools)
        declarations = [d for d in declarations if d.name in allowed_set]
    return [types.Tool(function_declarations=declarations)]
