"""Utility helpers shared across the broker package."""

from __future__ import annotations

import json
import os
from typing import Any, Dict


def read_env(key: str, default: str) -> str:
    """Return environment variable values with a simple default."""
    return os.environ.get(key, default)


def encode_message(payload: Dict[str, Any]) -> bytes:
    """Serialize a JSON payload into a newline-delimited byte string."""
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


def decode_message(raw_line: bytes) -> Dict[str, Any]:
    """Deserialize a JSON payload received from the wire."""
    try:
        return json.loads(raw_line.decode("utf-8").strip())
    except json.JSONDecodeError as exc:  # pragma: no cover - thin wrapper
        raise ValueError("Received malformed JSON payload") from exc
