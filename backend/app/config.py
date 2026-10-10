"""
Application configuration.

All settings are read from environment variables / .env file.
Model names, API keys, and operational parameters are fully configurable
without code changes.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from threading import Lock

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve .env relative to the repo root (two levels up from this file)
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """AgentBreak configuration — reads from .env at the repo root."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Gemini API ──────────────────────────────────────────────
    gemini_api_key: str = ""

    # Model names (swap without code changes)
    victim_model: str = "gemini-2.0-flash"
    attacker_model: str = "gemini-2.0-flash"
    classifier_model: str = "gemini-2.0-flash"

    # ── Temperatures ────────────────────────────────────────────
    victim_temperature: float = 0.1
    attacker_temperature: float = 0.8
    classifier_temperature: float = 0.0

    # ── Agent limits ────────────────────────────────────────────
    max_agent_steps: int = 8
    attack_budget_k: int = 10  # iterations per goal

    # ── API call management ─────────────────────────────────────
    request_budget: int = 500          # total API calls before hard stop
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0      # seconds, doubles each retry
    rate_limit_rpm: int = 15           # requests per minute guard

    # ── Database ────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./agentbreak.db"

    # ── Demo mode ───────────────────────────────────────────────
    demo_mode: bool = False


class BudgetCounter:
    """Thread-safe request budget counter."""

    def __init__(self, budget: int) -> None:
        self._remaining = budget
        self._lock = Lock()

    @property
    def remaining(self) -> int:
        return self._remaining

    def consume(self, n: int = 1) -> int:
        """Consume *n* from the budget. Returns remaining. Raises if exhausted."""
        with self._lock:
            if self._remaining < n:
                raise BudgetExhaustedError(
                    f"Request budget exhausted ({self._remaining} remaining, "
                    f"requested {n})"
                )
            self._remaining -= n
            return self._remaining


class BudgetExhaustedError(RuntimeError):
    """Raised when the global API-call budget hits zero."""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()


# Module-level budget counter, initialised lazily.
_budget: BudgetCounter | None = None


def get_budget() -> BudgetCounter:
    """Return the global budget counter, creating it on first call."""
    global _budget
    if _budget is None:
        _budget = BudgetCounter(get_settings().request_budget)
    return _budget
