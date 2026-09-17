"""CLI demo for XML-RPC add/mul/greet/inspect."""

from __future__ import annotations

import logging

from lab2.rpc_client import call
from lab2.rpc_server import RpcServer

logger = logging.getLogger(__name__)


def run_lab2() -> dict[str, object]:
    server = RpcServer()
    server.start()
    try:
        results = {
            "add": call("add", 2, 3),
            "mul": call("mul", 6, 7),
            "greet_student": call("greet_student"),
            "inspect_module": call("inspect_module"),
        }
        for key, value in results.items():
            logger.info("%s -> %s", key, value)
        return results
    finally:
        server.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_lab2()
