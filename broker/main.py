"""Entry point for the CodeSage broker."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from .handlers import BrokerServer
from .utils import read_env


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CodeSage local broker")
    parser.add_argument("--host", default=read_env("BROKER_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(read_env("BROKER_PORT", "5555")))
    parser.add_argument("--log-level", default=read_env("BROKER_LOG_LEVEL", "INFO"))
    return parser.parse_args(argv)


async def amain(args: argparse.Namespace) -> None:
    server = BrokerServer(args.host, args.port)
    await server.serve_forever()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level.upper(), format="%(levelname)s %(name)s: %(message)s")
    try:
        asyncio.run(amain(args))
    except KeyboardInterrupt:
        logging.info("Broker interrupted by user")


if __name__ == "__main__":
    main(sys.argv[1:])
