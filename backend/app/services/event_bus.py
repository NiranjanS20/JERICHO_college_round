"""
In-memory Server-Sent Events (SSE) event bus for AgentBreak campaigns.

Provides publish/subscribe queues, sequence numbering, and replay buffers per campaign_id.
Eliminates race conditions between campaign creation and SSE connection establishment.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from typing import Any, AsyncGenerator


class CampaignEventBus:
    """Manages active subscriber queues, sequence ordering, and replay history per campaign."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._sequence_counters: dict[str, int] = {}
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
        """Broadcast an event payload with monotonic sequence numbers and persist to history."""
        async with self._lock:
            seq = self._sequence_counters.get(campaign_id, 0) + 1
            self._sequence_counters[campaign_id] = seq
            
            event_copy = dict(event_data)
            event_copy["seq"] = seq
            event_copy["campaign_id"] = campaign_id
            if "timestamp" not in event_copy:
                event_copy["timestamp"] = datetime.now(timezone.utc).isoformat()

            if campaign_id not in self._history:
                self._history[campaign_id] = []
            self._history[campaign_id].append(event_copy)

            queues = list(self._subscribers.get(campaign_id, []))

        for q in queues:
            await q.put(event_copy)

    def get_history(self, campaign_id: str) -> list[dict[str, Any]]:
        """Return all published events for a campaign in sequence order."""
        return list(self._history.get(campaign_id, []))

    async def event_generator(
        self, campaign_id: str, last_seq: int = 0, timeout_seconds: float = 60.0
    ) -> AsyncGenerator[str, None]:
        """Async generator yielding formatted SSE strings with sequence-based replay."""
        queue = await self.subscribe(campaign_id)
        current_seq = last_seq

        try:
            # 1. Replay historical events that occurred before this subscription or since last_seq
            async with self._lock:
                historical_events = [
                    e for e in self._history.get(campaign_id, [])
                    if e.get("seq", 0) > current_seq
                ]

            is_terminal = False
            for event in historical_events:
                current_seq = max(current_seq, event.get("seq", 0))
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("event") in ("campaign_finished", "campaign_failed", "campaign_cancelled"):
                    is_terminal = True
                    break

            if is_terminal:
                return

            # 2. Stream new live events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=timeout_seconds)
                    evt_seq = event.get("seq", 0)
                    if evt_seq <= current_seq:
                        continue  # Skip events already replayed from history

                    current_seq = evt_seq
                    yield f"data: {json.dumps(event)}\n\n"
                    
                    if event.get("event") in ("campaign_finished", "campaign_failed", "campaign_cancelled"):
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat ping
                    yield ": heartbeat\n\n"
        finally:
            await self.unsubscribe(campaign_id, queue)


# Global singleton instance
event_bus = CampaignEventBus()
