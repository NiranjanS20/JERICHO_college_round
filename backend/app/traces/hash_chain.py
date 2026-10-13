"""
Hash-chain computation and seal generation for Domain 10 (Audit Integrity).

Computes sha256(prev_hash || canonical_json(event)) for tamper-evident trace logging.
Generates HMAC-SHA256 seals for completed runs.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def canonical_json(data: Any) -> str:
    """Serialize data into canonical JSON string with sorted keys and no whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_event_hash(prev_hash: str, payload: Any) -> str:
    """Compute sha256(prev_hash || canonical_json(payload)).

    Initial prev_hash at seq 0 MUST be 64 zeros ("0" * 64).
    """
    canonical_payload = canonical_json(payload)
    data = f"{prev_hash}{canonical_payload}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def generate_run_seal(run_id: str, head_hash: str, event_count: int, secret_key: str) -> str:
    """Generate an HMAC-SHA256 seal for a run over (run_id || head_hash || event_count)."""
    message = f"{run_id}:{head_hash}:{event_count}".encode("utf-8")
    key = secret_key.encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def verify_run_seal(run_id: str, head_hash: str, event_count: int, secret_key: str, expected_hmac: str) -> bool:
    """Verify an HMAC seal for a run."""
    computed_hmac = generate_run_seal(run_id, head_hash, event_count, secret_key)
    return hmac.compare_digest(computed_hmac, expected_hmac)


def verify_hash_chain(events: list[dict[str, Any]]) -> tuple[bool, str | None]:
    """Verify integrity of a hash-chained event log.
    
    Detects any modification, insertion, deletion, or reordering.
    Returns (True, None) if intact, or (False, reason) if corrupted.
    """
    if not events:
        return True, None

    expected_prev = "0" * 64

    for idx, evt in enumerate(events):
        prev_hash = evt.get("prev_hash")
        event_hash = evt.get("event_hash")
        payload = evt.get("payload")

        if prev_hash != expected_prev:
            return False, f"Broken link at sequence {idx}: expected prev_hash '{expected_prev[:12]}...', got '{str(prev_hash)[:12]}...'"

        computed = compute_event_hash(prev_hash, payload)
        if computed != event_hash:
            return False, f"Payload tampering detected at sequence {idx}: recomputed '{computed[:12]}...' != recorded '{str(event_hash)[:12]}...'"

        expected_prev = event_hash

    return True, None
