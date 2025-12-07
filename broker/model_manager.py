"""Model backend selection and llama.cpp integration."""

from __future__ import annotations

import asyncio
import logging
import threading
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterator, Optional, Tuple

from .utils import read_env, read_env_int, resolve_models_dir

try:  # pragma: no cover - optional dependency
    from llama_cpp import Llama
except ImportError:  # pragma: no cover - optional dependency
    Llama = None  # type: ignore[assignment]


LOGGER = logging.getLogger(__name__)
TokenChunk = Tuple[int, str]


class BaseBackend:
    """Interface for model backends."""

    name = "base"

    async def generate(self, prompt: str, **params: Any) -> str:
        raise NotImplementedError

    async def stream_tokens(self, prompt: str, **params: Any) -> AsyncIterator[TokenChunk]:
        raise NotImplementedError


class EchoBackend(BaseBackend):
    """Fallback backend that simply echoes the prompt."""

    name = "echo"

    async def generate(self, prompt: str, **params: Any) -> str:
        await asyncio.sleep(0)
        return prompt

    async def stream_tokens(self, prompt: str, **params: Any) -> AsyncIterator[TokenChunk]:
        await asyncio.sleep(0)
        if not prompt:
            return
        for idx, char in enumerate(prompt):
            yield idx, char


class LlamaBackend(BaseBackend):
    """Backend that drives llama.cpp via llama-cpp-python."""

    name = "llama"

    def __init__(self, model_path: Path, n_ctx: int, n_threads: int):
        if Llama is None:  # pragma: no cover - validated in ModelManager
            raise RuntimeError("llama-cpp-python is not installed")
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self._llama: Optional[Llama] = None  # type: ignore[valid-type]
        self._lock = threading.Lock()

    async def generate(self, prompt: str, **params: Any) -> str:
        llama_params = self._llama_params(params)
        return await asyncio.to_thread(self._generate_sync, prompt, llama_params)

    async def stream_tokens(self, prompt: str, **params: Any) -> AsyncIterator[TokenChunk]:
        llama_params = self._llama_params(params)
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Optional[TokenChunk]] = asyncio.Queue()

        def producer() -> None:
            try:
                for chunk in self._stream_sync(prompt, llama_params):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        threading.Thread(target=producer, daemon=True).start()

        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk

    def _ensure_model(self) -> Llama:
        if self._llama is None:
            with self._lock:
                if self._llama is None:
                    LOGGER.info("Loading llama.cpp model from %s", self.model_path)
                    self._llama = Llama(  # type: ignore[call-arg]
                        model_path=str(self.model_path),
                        n_ctx=self.n_ctx,
                        n_threads=self.n_threads,
                        logits_all=False,
                    )
        return self._llama  # type: ignore[return-value]

    def _generate_sync(self, prompt: str, params: Dict[str, Any]) -> str:
        llm = self._ensure_model()
        completion = llm.create_completion(prompt=prompt, stream=False, **params)
        return completion["choices"][0]["text"]

    def _stream_sync(self, prompt: str, params: Dict[str, Any]) -> Iterator[TokenChunk]:
        llm = self._ensure_model()
        for idx, packet in enumerate(llm.create_completion(prompt=prompt, stream=True, **params)):
            yield idx, packet["choices"][0]["text"]

    @staticmethod
    def _llama_params(params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "max_tokens": int(params.get("max_tokens", 256)),
            "temperature": float(params.get("temperature", 0.6)),
            "top_p": float(params.get("top_p", 0.95)),
            "stop": params.get("stop"),
        }


class ModelManager:
    """Selects and orchestrates model backends."""

    def __init__(
        self,
        backend: Optional[str] = None,
        model_path: Optional[str] = None,
        n_ctx: Optional[int] = None,
        n_threads: Optional[int] = None,
    ):
        requested_backend = (backend or read_env("BROKER_MODEL_BACKEND", "llama")).lower()
        models_dir = resolve_models_dir()
        default_model = models_dir / read_env("BROKER_MODEL_FILE", "code-llama-7b.gguf")
        resolved_model = Path(model_path or read_env("BROKER_MODEL_PATH", str(default_model)))
        resolved_model = resolved_model.expanduser().resolve()

        ctx = n_ctx or read_env_int("BROKER_CONTEXT", 4096)
        threads = n_threads or read_env_int("BROKER_THREADS", 4)

        self.backend = self._init_backend(requested_backend, resolved_model, ctx, threads)
        self.model_name = resolved_model.name if self.backend.name == "llama" else self.backend.name

    async def generate(self, prompt: str, **params: Any) -> Dict[str, Any]:
        copied_params = dict(params)
        output = await self.backend.generate(prompt, **copied_params)
        return self.format_result(prompt, copied_params, output)

    async def stream_tokens(self, prompt: str, **params: Any) -> AsyncIterator[TokenChunk]:
        async for chunk in self.backend.stream_tokens(prompt, **params):
            yield chunk

    def format_result(self, prompt: str, params: Dict[str, Any], output: str) -> Dict[str, Any]:
        return {
            "model": self.model_name,
            "prompt": prompt,
            "params": params,
            "output": output,
        }

    def _init_backend(
        self,
        backend: str,
        model_path: Path,
        n_ctx: int,
        n_threads: int,
    ) -> BaseBackend:
        if backend == "llama":
            if Llama is None:
                LOGGER.warning("llama-cpp-python unavailable; falling back to echo backend")
                return EchoBackend()
            if not model_path.exists():
                LOGGER.warning("Model %s missing; falling back to echo backend", model_path)
                return EchoBackend()
            return LlamaBackend(model_path, n_ctx, n_threads)

        if backend != "echo":
            LOGGER.warning("Unknown backend '%s'; defaulting to echo backend", backend)
        return EchoBackend()
