"""
Kill Switch (INC-01).
Provides global or campaign-level abort signals.
"""
import asyncio

class KillSwitch:
    _switches: dict[str, asyncio.Event] = {}

    @classmethod
    def get(cls, campaign_id: str) -> asyncio.Event:
        if campaign_id not in cls._switches:
            cls._switches[campaign_id] = asyncio.Event()
        return cls._switches[campaign_id]

    @classmethod
    def kill(cls, campaign_id: str) -> None:
        if campaign_id in cls._switches:
            cls._switches[campaign_id].set()

    @classmethod
    def is_killed(cls, campaign_id: str) -> bool:
        return cls.get(campaign_id).is_set()
