"""
Centralised Gemini LLM client.
Provides async execution, exponential backoff, budget enforcement,
error classification, connectivity verification, and live/offline metrics.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Any

from google import genai
from google.genai import types

from app.config import get_settings, get_budget, BudgetExhaustedError

logger = logging.getLogger(__name__)


# ── Specific Gemini Exception Hierarchy ──────────────────────────────────
class GeminiError(RuntimeError):
    """Base exception for Gemini LLM client errors."""
    pass

class GeminiAuthError(GeminiError):
    """Raised on invalid API key or permission denied."""
    pass

class GeminiQuotaError(GeminiError):
    """Raised when rate limit or quota is exhausted (429/RESOURCE_EXHAUSTED)."""
    pass

class GeminiTimeoutError(GeminiError):
    """Raised when a generation request times out."""
    pass

class GeminiModelNotFoundError(GeminiError):
    """Raised when the requested model identifier is invalid or unsupported."""
    pass


def classify_gemini_exception(exc: Exception) -> GeminiError:
    """Classify underlying exception into explicit GeminiError without leaking secrets."""
    msg = str(exc)
    msg_lower = msg.lower()

    if "401" in msg or "403" in msg or "api_key_invalid" in msg_lower or "api key not valid" in msg_lower:
        return GeminiAuthError("Gemini authentication failed: invalid or unauthorized API key.")
    if "429" in msg or "resource_exhausted" in msg_lower or "quota" in msg_lower:
        return GeminiQuotaError("Gemini quota or rate limit exhausted.")
    if "404" in msg or "not_found" in msg_lower or "model not found" in msg_lower:
        return GeminiModelNotFoundError(f"Requested Gemini model not found or unsupported.")
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)) or "deadline_exceeded" in msg_lower or "timed out" in msg_lower:
        return GeminiTimeoutError("Gemini request timed out.")
    return GeminiError(f"Gemini API error: {type(exc).__name__}")


class GeminiClient:
    """Singleton wrapper for Google GenAI client with guardrails and telemetry."""
    
    _instance: GeminiClient | None = None
    
    @classmethod
    def get_instance(cls) -> GeminiClient:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (primarily for testing)."""
        cls._instance = None
        
    def __init__(self) -> None:
        self.settings = get_settings()
        self.budget = get_budget()
        has_key = bool(
            self.settings.gemini_api_key
            and self.settings.gemini_api_key != "your-api-key-here"
            and not self.settings.demo_mode
        )
        self.client = genai.Client(api_key=self.settings.gemini_api_key) if has_key else None
        # Concurrency limit
        self._semaphore = asyncio.Semaphore(10)
        # Call counters
        self.call_counts = {
            "live": 0,
            "offline": 0,
            "failed": 0,
        }
        self._last_connectivity_check: dict[str, Any] | None = None

    def is_configured(self) -> bool:
        """Return True if a valid API key is present and demo mode is not active."""
        return self.client is not None

    async def get_health_status(self, test_connectivity: bool = False) -> dict[str, Any]:
        """Return safe health check dictionary without revealing credentials."""
        configured = self.is_configured()
        mode = "offline" if self.settings.demo_mode else ("live" if configured else "offline")
        
        status_info: dict[str, Any] = {
            "status": "healthy" if configured else "offline",
            "provider": "gemini",
            "configured": configured,
            "mode": mode,
            "demo_mode": self.settings.demo_mode,
            "models": {
                "victim": self.settings.victim_model,
                "attacker": self.settings.attacker_model,
                "classifier": self.settings.classifier_model,
            },
            "call_counts": dict(self.call_counts),
            "connectivity": "offline" if not configured else ("verified" if self._last_connectivity_check and self._last_connectivity_check.get("success") else "unverified"),
            "error": None,
        }

        if test_connectivity and configured:
            check_res = await self.check_connectivity()
            status_info["connectivity"] = "verified" if check_res["success"] else "error"
            status_info["error"] = check_res.get("error")

        return status_info

    async def check_connectivity(self, model: str | None = None) -> dict[str, Any]:
        """Perform a lightweight live check to verify credentials and model connectivity."""
        if not self.client:
            return {
                "success": False,
                "error": "Gemini client not configured or demo mode active",
                "execution_mode": "offline",
            }

        target_model = model or self.settings.victim_model
        try:
            # Use small ping prompt with timeout to minimize latency & cost
            config = types.GenerateContentConfig(
                max_output_tokens=5,
                temperature=0.0,
            )
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=target_model,
                    contents="ping",
                    config=config,
                ),
                timeout=10.0,
            )
            self._last_connectivity_check = {"success": True, "error": None}
            return {
                "success": True,
                "model": target_model,
                "execution_mode": "live",
                "error": None,
            }
        except Exception as exc:
            classified = classify_gemini_exception(exc)
            err_msg = str(classified)
            self._last_connectivity_check = {"success": False, "error": err_msg}
            logger.error(f"Gemini connectivity check failed: {err_msg}")
            return {
                "success": False,
                "model": target_model,
                "execution_mode": "failed",
                "error": err_msg,
            }

    async def generate_content(
        self,
        model: str,
        contents: Any,
        config: types.GenerateContentConfig | None = None,
        timeout: float = 30.0,
        strict_live: bool = False,
    ) -> types.GenerateContentResponse | None:
        """Call Gemini API with backoff, budget enforcement, and explicit error handling."""
        if not self.client:
            self.call_counts["offline"] += 1
            if strict_live:
                raise GeminiError("Live Gemini requested but client is unconfigured or in demo mode.")
            return None
            
        last_exc: Exception | None = None
        
        async with self._semaphore:
            for attempt in range(self.settings.retry_max_attempts):
                self.budget.consume(1)
                
                try:
                    res = await asyncio.wait_for(
                        self.client.aio.models.generate_content(
                            model=model,
                            contents=contents,
                            config=config,
                        ),
                        timeout=timeout,
                    )
                    self.call_counts["live"] += 1
                    return res
                except BudgetExhaustedError:
                    self.call_counts["failed"] += 1
                    raise
                except Exception as exc:
                    last_exc = exc
                    classified = classify_gemini_exception(exc)
                    is_rate_limit = isinstance(classified, GeminiQuotaError)
                    is_fatal_auth = isinstance(classified, GeminiAuthError)
                    is_fatal_model = isinstance(classified, GeminiModelNotFoundError)

                    # Fatal errors do not benefit from retrying
                    if is_fatal_auth or is_fatal_model:
                        self.call_counts["failed"] += 1
                        raise classified from exc

                    delay = self.settings.retry_base_delay * (2 ** attempt)
                    if is_rate_limit:
                        logger.warning(
                            "Rate limited (attempt %d/%d), sleeping %.1fs",
                            attempt + 1, self.settings.retry_max_attempts, delay,
                        )
                    else:
                        logger.warning(
                            "Gemini error (attempt %d/%d): %s — retrying in %.1fs",
                            attempt + 1, self.settings.retry_max_attempts, classified, delay,
                        )

                    if attempt < self.settings.retry_max_attempts - 1:
                        await asyncio.sleep(delay)
                    
        self.call_counts["failed"] += 1
        classified_final = classify_gemini_exception(last_exc) if last_exc else GeminiError("Unknown failure")
        raise classified_final from last_exc
