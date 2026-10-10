"""
Kill Switch (INC-01).
Provides global or campaign-level abort signals.
"""
import asyncio

class KillSwitch:
    _switches: dict[str, asyncio.Event] = {}
    _global_killed: bool = False
    _global_reason: str = ""

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
    def trigger_global(cls, reason: str = "Safety Lead triggered global emergency stop") -> None:
        cls._global_killed = True
        cls._global_reason = reason
        for ev in cls._switches.values():
            ev.set()

    @classmethod
    def reset_global(cls) -> None:
        cls._global_killed = False
        cls._global_reason = ""
        cls._switches.clear()

    @classmethod
    def is_globally_killed(cls) -> bool:
        return cls._global_killed

    @classmethod
    def get_global_status(cls) -> dict:
        return {
            "active": cls._global_killed,
            "reason": cls._global_reason,
            "active_campaign_locks": len(cls._switches),
        }

    @classmethod
    def is_killed(cls, campaign_id: str) -> bool:
        if cls._global_killed:
            return True
        return cls.get(campaign_id).is_set()
