"""
Unit tests for the Victim Agent sandbox, fake data, memory, and mocked tools.
"""

from __future__ import annotations

import pytest

from app.victim import fake_data
from app.victim.memory import MemoryStore
from app.victim.policy import ALLOWED_TOOLS, POLICY_RULES, SENSITIVE_TOOLS, SYSTEM_PROMPT
from app.victim.tools import (
    TOOL_REGISTRY,
    clear_call_log,
    get_call_log,
    get_tool_declarations,
    query_customer_db,
    read_email,
    read_memory,
    search_docs,
    send_email,
    set_session_id,
    write_memory,
)


def test_fake_data_canaries() -> None:
    """Canary secrets must be present and embedded in the system prompt."""
    assert len(fake_data.CANARY_SECRETS) >= 4
    for key, secret in fake_data.CANARY_SECRETS.items():
        assert secret in fake_data.CANARY_STRINGS
        assert secret in SYSTEM_PROMPT


def test_fake_data_lookups() -> None:
    """Document search and email retrieval from fake data."""
    # Search documents
    docs = fake_data.search_documents("handbook")
    assert len(docs) >= 1
    assert "Employee Handbook" in str(docs[0]["title"])

    # Search customer
    customers = fake_data.CUSTOMERS
    assert len(customers) >= 5

    # Get email
    email = fake_data.get_email("EMAIL-001")
    assert email is not None
    assert email["subject"] == "Q3 Budget Review"


@pytest.mark.asyncio
async def test_memory_store_operations() -> None:
    """Memory store should support writing, reading, and clearing per session."""
    store = MemoryStore.get_or_create("test-session-1")
    await store.clear()

    await store.write("note1", "meeting at 3pm")
    val = await store.read("note1")
    assert val == "meeting at 3pm"

    all_data = await store.read_all()
    assert all_data == {"note1": "meeting at 3pm"}

    await store.clear()
    assert await store.read("note1") is None


@pytest.mark.asyncio
async def test_mocked_tools_logging() -> None:
    """Every mocked tool invocation must be logged with args and results."""
    clear_call_log()
    set_session_id("test-session-tools")

    # 1. read_email
    email_res = await read_email("EMAIL-001")
    assert "subject" in email_res

    # 2. send_email
    send_res = await send_email("alice@acme.com", "Test", "Body content")
    assert send_res["status"] == "sent"

    # 3. search_docs
    docs_res = await search_docs("handbook")
    assert len(docs_res) > 0

    # 4. query_customer_db
    cust_res = await query_customer_db("Alice")
    assert len(cust_res) >= 1

    # 5. write_memory and read_memory
    await write_memory("fav_color", "blue")
    mem_res = await read_memory()
    assert mem_res.get("fav_color") == "blue"

    # Verify log entries
    log = get_call_log()
    assert len(log) == 6
    logged_names = [call.tool_name for call in log]
    assert logged_names == [
        "read_email",
        "send_email",
        "search_docs",
        "query_customer_db",
        "write_memory",
        "read_memory",
    ]


def test_tool_declarations() -> None:
    """Tool declarations must match the tool registry."""
    tools = get_tool_declarations()
    assert len(tools) > 0
    # Gemini tool contains function_declarations
    assert len(tools[0].function_declarations) == len(TOOL_REGISTRY)
    names = {fn.name for fn in tools[0].function_declarations}
    assert names == ALLOWED_TOOLS

