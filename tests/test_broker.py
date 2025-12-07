import unittest

from broker.model_manager import ModelManager
from broker.utils import decode_message, encode_message


class ModelManagerTests(unittest.IsolatedAsyncioTestCase):
    async def test_echo_generate_returns_prompt(self) -> None:
        manager = ModelManager(backend="echo")
        result = await manager.generate("Hello CodeSage")
        self.assertEqual(result["output"], "Hello CodeSage")
        self.assertEqual(result["model"], "echo")

    async def test_stream_tokens_round_trip(self) -> None:
        manager = ModelManager(backend="echo")
        tokens = []
        async for _, token in manager.stream_tokens("abc"):
            tokens.append(token)
        self.assertEqual("".join(tokens), "abc")


class UtilsTests(unittest.TestCase):
    def test_encode_decode_roundtrip(self) -> None:
        payload = {"type": "pong", "message": "ok"}
        encoded = encode_message(payload)
        self.assertEqual(payload, decode_message(encoded))


if __name__ == "__main__":
    unittest.main()
