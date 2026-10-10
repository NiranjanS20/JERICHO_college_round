"""
Checkpoint Store (LOG-03).
Provides isolated write-protected storage for trace seals.
"""
import os
import json
from pathlib import Path
from typing import Any

CHECKPOINT_DIR = Path("checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)

class CheckpointStore:
    @classmethod
    def save(cls, run_id: str, data: dict[str, Any]) -> None:
        path = CHECKPOINT_DIR / f"{run_id}.json"
        if path.exists():
            raise FileExistsError(f"Checkpoint for {run_id} already exists (write-protected).")
        with open(path, "w") as f:
            json.dump(data, f)
            
    @classmethod
    def load(cls, run_id: str) -> dict[str, Any] | None:
        path = CHECKPOINT_DIR / f"{run_id}.json"
        if not path.exists():
            return None
        with open(path, "r") as f:
            return json.load(f)
