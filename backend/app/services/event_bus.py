"""
In-memory Server-Sent Events (SSE) event bus for AgentBreak campaigns.

Provides publish/subscribe queues per campaign_id so that running campaigns
can broadcast progress events (attack_started, step, tool_call, oracle_verdict, etc.)
to connected web clients in real time.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator


class CampaignEventBus:
    """Manages active subscriber queues per campaign."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, campaign_id: str) -> asyncio.Queue[dict[str, Any]]:
        """Register a new listener queue for a campaign."""
        async with self._lock:
            queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
            if campaign_id not in self._subscribers:
                self._subscribers[campaign_id] = []
            self._subscribers[campaign_id].append(queue)
            return queue

    async def unsubscribe(self, campaign_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Remove a listener queue."""
        async with self._lock:
            if campaign_id in self._subscribers:
                try:
                    self._subscribers[campaign_id].remove(queue)
                except ValueError:
                    pass
                if not self._subscribers[campaign_id]:
                    del self._subscribers[campaign_id]

    async def publish(self, campaign_id: str, event_data: dict[str, Any]) -> None:
        """Broadcast an event payload to all active subscribers for the campaign."""
        async with self._lock:
            queues = list(self._subscribers.get(campaign_id, []))
        for q in queues:
            await q.put(event_data)

    async def event_generator(
        self, campaign_id: str, timeout_seconds: float = 60.0
    ) -> AsyncGenerator[str, None]:
        """Async generator yielding formatted SSE data strings."""
        queue = await self.subscribe(campaign_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=timeout_seconds)
                    yield f"data: {json.dumps(event)}\n\n"
                    # If this is the terminal campaign finished event, break
                    if event.get("event") == "campaign_finished":
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat ping
                    yield f": heartbeat\n\n"
        finally:
            await self.unsubscribe(campaign_id, queue)


# Global singleton instance
event_bus = CampaignEventBus()

