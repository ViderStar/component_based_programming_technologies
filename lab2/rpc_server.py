"""XML-RPC server: arithmetic, student greeting, module introspection."""

from __future__ import annotations

import inspect
import logging
import threading
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

from configs.cfg import DEFAULT_STUDENT, LAB2_HOST, LAB2_PORT

logger = logging.getLogger(__name__)


class QuietXMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/", "/RPC2")


class MathService:
    def add(self, x: float, y: float) -> float:
        return x + y

    def mul(self, x: float, y: float) -> float:
        return x * y

    def greet_student(self, name: str = "", group: str = "") -> str:
        person = name or DEFAULT_STUDENT["name"]
        grp = group or DEFAULT_STUDENT["group"]
        return f"Hello, from {person} ({grp})"

    def inspect_module(self) -> dict[str, str]:
        members: dict[str, str] = {}
        for name, value in inspect.getmembers(self):
            if name.startswith("_"):
                continue
            if inspect.ismethod(value) or inspect.isfunction(value):
                members[name] = str(inspect.signature(value))
        return members


class RpcServer:
    def __init__(self, host: str = LAB2_HOST, port: int = LAB2_PORT) -> None:
        self.host = host
        self.port = port
        self._server: SimpleXMLRPCServer | None = None
        self._thread: threading.Thread | None = None
        self.service = MathService()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._server = SimpleXMLRPCServer(
            (self.host, self.port),
            requestHandler=QuietXMLRPCRequestHandler,
            allow_none=True,
            logRequests=False,
        )
        self._server.register_introspection_functions()
        self._server.register_instance(self.service)
        self._thread = threading.Thread(target=self._server.serve_forever, name="lab2-rpc", daemon=True)
        self._thread.start()
        logger.info("XML-RPC listening on http://%s:%s/", self.host, self.port)

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._server = None
        self._thread = None
