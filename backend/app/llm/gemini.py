"""
Centralised Gemini LLM client.
Provides async execution, exponential backoff, and concurrency limits.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Any

from google import genai
from google.genai import types

from app.config import get_settings, get_budget, BudgetExhaustedError

logger = logging.getLogger(__name__)

class GeminiClient:
    """Singleton wrapper for Google GenAI client with guardrails."""
    
    _instance: GeminiClient | None = None
    
    @classmethod
    def get_instance(cls) -> GeminiClient:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def __init__(self) -> None:
        self.settings = get_settings()
        self.budget = get_budget()
        has_key = bool(
            self.settings.gemini_api_key
            and self.settings.gemini_api_key != "your-api-key-here"
            and not self.settings.demo_mode
        )
        self.client = genai.Client(api_key=self.settings.gemini_api_key) if has_key else None
        # Limit concurrent LLM calls to prevent sudden spikes
        self._semaphore = asyncio.Semaphore(10)
        
    async def generate_content(
        self,
        model: str,
        contents: list[types.Content] | str,
        config: types.GenerateContentConfig | None = None
    ) -> types.GenerateContentResponse | None:
        """Call Gemini API with backoff and budget checks. Returns None in offline mode."""
        if not self.client:
            return None
            
        last_exc: Exception | None = None
        
        async with self._semaphore:
            for attempt in range(self.settings.retry_max_attempts):
                self.budget.consume(1)
                
                try:
                    return await self.client.aio.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config
                    )
                except Exception as exc:
                    last_exc = exc
                    is_rate_limit = "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)
                    delay = self.settings.retry_base_delay * (2 ** attempt)
                    if is_rate_limit:
                        logger.warning("Rate limited (attempt %d/%d), sleeping %.1fs",
                                       attempt + 1, self.settings.retry_max_attempts, delay)
                    else:
                        logger.warning("Gemini error (attempt %d/%d): %s — retrying in %.1fs",
                                       attempt + 1, self.settings.retry_max_attempts, exc, delay)
                    await asyncio.sleep(delay)
                    
        raise RuntimeError(
            f"Gemini API call failed after {self.settings.retry_max_attempts} attempts: {last_exc}"
        ) from last_exc
