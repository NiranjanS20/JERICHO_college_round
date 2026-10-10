"""
Pytest fixtures and configuration for AgentBreak tests.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Set test environment variables
os.environ["GEMINI_API_KEY"] = "mock-gemini-key-for-tests"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DEMO_MODE"] = "true"


@pytest.fixture
def mock_settings(monkeypatch):
    """Fixture providing test settings."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key-for-tests")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from app.config import get_settings
    return get_settings()

