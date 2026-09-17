"""Python XML-RPC client used by GUI, CLI, and tests."""

from __future__ import annotations

import xmlrpc.client
from typing import Any

from configs.cfg import LAB2_HOST, LAB2_PORT


def make_proxy(host: str = LAB2_HOST, port: int = LAB2_PORT) -> xmlrpc.client.ServerProxy:
    return xmlrpc.client.ServerProxy(f"http://{host}:{port}/", allow_none=True)


def call(method: str, *args: Any, host: str = LAB2_HOST, port: int = LAB2_PORT) -> Any:
    proxy = make_proxy(host, port)
    func = getattr(proxy, method)
    return func(*args)
