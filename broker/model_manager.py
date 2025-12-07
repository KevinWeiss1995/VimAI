"""Lightweight model manager placeholder.

For STEP 2 we keep things intentionally simple: the "model" just echoes the
incoming prompt. The API mirrors what a real backend would look like so the
rest of the system can evolve without churn.
"""

from __future__ import annotations

from typing import Any, Dict


class ModelManager:
    """Stub model manager that returns an echo response."""

    def __init__(self, model_name: str = "echo"):
        self.model_name = model_name

    async def generate(self, prompt: str, **params: Any) -> Dict[str, Any]:
        """Pretend to run a model and return an echo payload."""
        return {
            "model": self.model_name,
            "prompt": prompt,
            "params": params,
            "output": prompt,
        }
