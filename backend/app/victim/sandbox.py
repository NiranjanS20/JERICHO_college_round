"""
Sandbox Factory.
Constructs temporary isolated environments for the agent to run in.
"""
from __future__ import annotations
from contextlib import contextmanager
from typing import Generator
import uuid

@contextmanager
def sandbox_context(fixture_id: str = "default", seed: int = 42) -> Generator[str, None, None]:
    """
    Context manager that provisions a temporary sandbox (e.g., in-memory SQLite)
    and tears it down afterward.
    
    Yields a session ID or connection string.
    """
    session_id = f"sandbox-{uuid.uuid4().hex[:8]}"
    # TODO: Initialize ephemeral SQLite DB with the fixture data here
    try:
        yield session_id
    finally:
        # TODO: Destroy ephemeral SQLite DB here
        pass
