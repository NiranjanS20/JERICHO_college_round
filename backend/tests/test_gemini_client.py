"""
Unit tests for GeminiClient, health check endpoints, and exception handling.
Verifies error classification, retry backoff, timeouts, and safe secret masking.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.config import Settings, BudgetCounter, BudgetExhaustedError
from app.llm.gemini import (
    GeminiClient,
    GeminiError,
    GeminiAuthError,
    GeminiQuotaError,
    GeminiTimeoutError,
    GeminiModelNotFoundError,
    classify_gemini_exception,
)


@pytest.fixture(autouse=True)
def reset_gemini_singleton():
    """Ensure GeminiClient singleton is reset between tests."""
    GeminiClient.reset_instance()
    yield
    GeminiClient.reset_instance()


def test_classify_gemini_exception():
    assert isinstance(classify_gemini_exception(Exception("API_KEY_INVALID: bad key")), GeminiAuthError)
    assert isinstance(classify_gemini_exception(Exception("401 Unauthorized")), GeminiAuthError)
    assert isinstance(classify_gemini_exception(Exception("429 RESOURCE_EXHAUSTED")), GeminiQuotaError)
    assert isinstance(classify_gemini_exception(Exception("404 Model not found: foo")), GeminiModelNotFoundError)
    assert isinstance(classify_gemini_exception(asyncio.TimeoutError()), GeminiTimeoutError)
    assert isinstance(classify_gemini_exception(Exception("Random database crash")), GeminiError)


@pytest.mark.asyncio
async def test_unconfigured_client_returns_none_in_offline_mode():
    with patch("app.llm.gemini.get_settings") as mock_settings:
        mock_settings.return_value = Settings(gemini_api_key="", demo_mode=False)
        client = GeminiClient()
        assert not client.is_configured()
        res = await client.generate_content("gemini-3.8-flash", "hello")
        assert res is None
        assert client.call_counts["offline"] == 1


@pytest.mark.asyncio
async def test_demo_mode_client_returns_none():
    with patch("app.llm.gemini.get_settings") as mock_settings:
        mock_settings.return_value = Settings(gemini_api_key="valid-looking-key", demo_mode=True)
        client = GeminiClient()
        assert not client.is_configured()
        health = await client.get_health_status()
        assert health["mode"] == "offline"
        assert health["demo_mode"] is True


@pytest.mark.asyncio
async def test_strict_live_raises_when_unconfigured():
    with patch("app.llm.gemini.get_settings") as mock_settings:
        mock_settings.return_value = Settings(gemini_api_key="", demo_mode=False)
        client = GeminiClient()
        with pytest.raises(GeminiError, match="Live Gemini requested"):
            await client.generate_content("gemini-3.8-flash", "hello", strict_live=True)


@pytest.mark.asyncio
async def test_successful_generate_content():
    fake_response = MagicMock()
    fake_response.text = "Hello from Gemini"

    with patch("app.llm.gemini.get_settings") as mock_settings, \
         patch("app.llm.gemini.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(gemini_api_key="test-key", demo_mode=False)
        mock_client_instance = MagicMock()
        mock_client_instance.aio.models.generate_content = AsyncMock(return_value=fake_response)
        mock_genai_client.return_value = mock_client_instance

        client = GeminiClient()
        assert client.is_configured()
        res = await client.generate_content("gemini-3.8-flash", "hi")
        assert res.text == "Hello from Gemini"
        assert client.call_counts["live"] == 1


@pytest.mark.asyncio
async def test_auth_error_aborts_without_retry():
    with patch("app.llm.gemini.get_settings") as mock_settings, \
         patch("app.llm.gemini.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(gemini_api_key="bad-key", demo_mode=False)
        mock_client_instance = MagicMock()
        mock_client_instance.aio.models.generate_content = AsyncMock(side_effect=Exception("API_KEY_INVALID: key not found"))
        mock_genai_client.return_value = mock_client_instance

        client = GeminiClient()
        with pytest.raises(GeminiAuthError):
            await client.generate_content("gemini-3.8-flash", "hi")
        
        # Immediate abort on auth failure — only 1 call attempt
        assert mock_client_instance.aio.models.generate_content.call_count == 1
        assert client.call_counts["failed"] == 1


@pytest.mark.asyncio
async def test_transient_error_retries_and_succeeds():
    fake_response = MagicMock()
    fake_response.text = "Success after retry"

    with patch("app.llm.gemini.get_settings") as mock_settings, \
         patch("app.llm.gemini.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(
            gemini_api_key="test-key",
            demo_mode=False,
            retry_max_attempts=3,
            retry_base_delay=0.01,
        )
        mock_client_instance = MagicMock()
        mock_client_instance.aio.models.generate_content = AsyncMock(
            side_effect=[Exception("Server error 500"), fake_response]
        )
        mock_genai_client.return_value = mock_client_instance

        client = GeminiClient()
        res = await client.generate_content("gemini-3.8-flash", "test prompt")
        assert res.text == "Success after retry"
        assert mock_client_instance.aio.models.generate_content.call_count == 2
        assert client.call_counts["live"] == 1


@pytest.mark.asyncio
async def test_timeout_classified_and_handled():
    with patch("app.llm.gemini.get_settings") as mock_settings, \
         patch("app.llm.gemini.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(
            gemini_api_key="test-key",
            demo_mode=False,
            retry_max_attempts=1,
        )
        mock_client_instance = MagicMock()
        mock_client_instance.aio.models.generate_content = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_genai_client.return_value = mock_client_instance

        client = GeminiClient()
        with pytest.raises(GeminiTimeoutError):
            await client.generate_content("gemini-3.8-flash", "prompt", timeout=0.01)
        assert client.call_counts["failed"] == 1


@pytest.mark.asyncio
async def test_budget_exhaustion_raises():
    with patch("app.llm.gemini.get_settings") as mock_settings, \
         patch("app.llm.gemini.get_budget") as mock_get_budget, \
         patch("app.llm.gemini.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(gemini_api_key="test-key", demo_mode=False)
        empty_budget = BudgetCounter(budget=0)
        mock_get_budget.return_value = empty_budget
        mock_genai_client.return_value = MagicMock()

        client = GeminiClient()
        client.budget = empty_budget
        with pytest.raises(BudgetExhaustedError):
            await client.generate_content("gemini-3.8-flash", "prompt")


@pytest.mark.asyncio
async def test_model_not_found_aborts_without_retry():
    """Verify GeminiModelNotFoundError aborts immediately on 404 model not found."""
    with patch("app.llm.gemini.get_settings") as mock_settings, \
         patch("app.llm.gemini.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(gemini_api_key="valid-key", demo_mode=False)
        mock_client_instance = MagicMock()
        mock_client_instance.aio.models.generate_content = AsyncMock(
            side_effect=Exception("404 models/gemini-unsupported-v99 is not found for API version")
        )
        mock_genai_client.return_value = mock_client_instance

        client = GeminiClient()
        with pytest.raises(GeminiModelNotFoundError):
            await client.generate_content("gemini-unsupported-v99", "hello")

        # Immediate abort — only 1 call attempt
        assert mock_client_instance.aio.models.generate_content.call_count == 1
        assert client.call_counts["failed"] == 1


@pytest.mark.asyncio
async def test_attacker_engine_malformed_json_fallback():
    """Verify attacker engine falls back to deterministic mutators if LLM returns malformed JSON."""
    from app.attacker.engine import AdaptiveAttackEngine

    fake_response = MagicMock()
    fake_response.text = "NOT VALID JSON AT ALL {unclosed: invalid"

    with patch("app.llm.gemini.get_settings") as mock_settings, \
         patch("app.llm.gemini.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(gemini_api_key="valid-key", demo_mode=False)
        mock_client_instance = MagicMock()
        mock_client_instance.aio.models.generate_content = AsyncMock(return_value=fake_response)
        mock_genai_client.return_value = mock_client_instance

        engine = AdaptiveAttackEngine()
        strategy, injection_pt, payload, reasoning = await engine._generate_payload(
            goal="Test exfiltration of data",
            current_strategy="direct_prompt_injection",
            iteration=1,
            feedback=[],
            best_attempt=None,
        )

        assert payload != ""
        assert strategy in ("direct_prompt_injection", "authority_impersonation")
        assert len(reasoning) > 0
