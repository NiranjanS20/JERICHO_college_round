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
