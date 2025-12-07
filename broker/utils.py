"""Utility helpers shared across the broker package."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def read_env(key: str, default: str) -> str:
    """Return environment variable values with a simple default."""
    return os.environ.get(key, default)


def read_env_int(key: str, default: int) -> int:
    """Read an integer environment variable with a fallback."""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def resolve_models_dir(default: str = "./models") -> Path:
    """Resolve the models directory location."""
    return Path(read_env("MODELS_DIR", default)).expanduser().resolve()


def encode_message(payload: Dict[str, Any]) -> bytes:
    """Serialize a JSON payload into a newline-delimited byte string."""
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


def decode_message(raw_line: bytes) -> Dict[str, Any]:
    """Deserialize a JSON payload received from the wire."""
    try:
        return json.loads(raw_line.decode("utf-8").strip())
    except json.JSONDecodeError as exc:  # pragma: no cover - thin wrapper
        raise ValueError("Received malformed JSON payload") from exc
