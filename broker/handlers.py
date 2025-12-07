"""Asyncio TCP server helpers for the broker."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Tuple

from .model_manager import ModelManager
from .utils import decode_message, encode_message

LOGGER = logging.getLogger(__name__)


class BrokerServer:
    """Thin wrapper around asyncio.start_server with JSON helpers."""

    def __init__(self, host: str, port: int, model_manager: Optional[ModelManager] = None):
        self.host = host
        self.port = port
        self.model_manager = model_manager or ModelManager()
        self._server: Optional[asyncio.AbstractServer] = None

    async def start(self) -> asyncio.AbstractServer:
        """Start listening but do not block."""
        if self._server:
            return self._server
        self._server = await asyncio.start_server(self._handle_client, self.host, self.port)
        sockets = ", ".join(self._format_socket(sock) for sock in self._server.sockets or [])
        LOGGER.info("Broker listening on %s", sockets or f"{self.host}:{self.port}")
        return self._server

    async def serve_forever(self) -> None:
        """Start the server (if needed) and block forever."""
        server = await self.start()
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        LOGGER.debug("Client connected: %s", peer)
        try:
            while True:
                raw_line = await reader.readline()
                if not raw_line:
                    break

                try:
                    request = decode_message(raw_line)
                except ValueError as exc:
                    LOGGER.warning("Dropping bad payload from %s: %s", peer, exc)
                    writer.write(encode_message({"type": "error", "message": "invalid_json"}))
                    await writer.drain()
                    continue

                await self._process_request(request, writer)
        except asyncio.CancelledError:  # pragma: no cover - shutdown path
            raise
        except Exception:
            LOGGER.exception("Unhandled exception while talking to %s", peer)
        finally:
            writer.close()
            await writer.wait_closed()
            LOGGER.debug("Client disconnected: %s", peer)

    async def _process_request(self, request: Dict[str, Any], writer: asyncio.StreamWriter) -> None:
        """Route incoming requests to the right handler."""
        kind = request.get("type", "completion")
        if kind == "ping":
            writer.write(encode_message({"type": "pong"}))
            await writer.drain()
            return
        if kind != "completion":
            writer.write(encode_message({"type": "error", "message": "unknown_request"}))
            await writer.drain()
            return

        await self._handle_completion(request, writer)

    async def _handle_completion(self, request: Dict[str, Any], writer: asyncio.StreamWriter) -> None:
        prompt = request.get("prompt") or ""
        params = dict(request.get("params") or {})
        stream_flag = request.get("stream")
        if stream_flag is None:
            stream = bool(params.pop("stream", True))
        else:
            stream = bool(stream_flag)
            params.pop("stream", None)

        if stream:
            await self._stream_completion(prompt, params, writer)
        else:
            result = await self.model_manager.generate(prompt, **params)
            writer.write(encode_message({"type": "completion", "result": result}))
            await writer.drain()

    async def _stream_completion(
        self,
        prompt: str,
        params: Dict[str, Any],
        writer: asyncio.StreamWriter,
    ) -> None:
        tokens: list[str] = []
        async for index, token in self.model_manager.stream_tokens(prompt, **params):
            tokens.append(token)
            writer.write(encode_message({"type": "token", "index": index, "token": token}))
            await writer.drain()

        result = self.model_manager.format_result(prompt, params, "".join(tokens))
        writer.write(encode_message({"type": "completion", "result": result}))
        await writer.drain()

    @staticmethod
    def _format_socket(sock: Any) -> str:
        host, port = BrokerServer._decode_sock(sock.getsockname())
        return f"{host}:{port}"

    @staticmethod
    def _decode_sock(sockname: Tuple[Any, ...]) -> Tuple[str, int]:
        host, port = sockname[:2]
        return str(host), int(port)
