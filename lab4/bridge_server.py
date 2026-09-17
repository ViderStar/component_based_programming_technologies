"""TCP JSON bridge: Java (or any client) sends {method, args} and Python uses getattr."""

from __future__ import annotations

import json
import logging
import socket
import threading
from typing import Any

from configs.cfg import LAB4_HOST, LAB4_PORT
from lab4.dynamic_student import make_student
from lab4.runtime_methods import add_method_to_object, introduce

logger = logging.getLogger(__name__)


class MethodBridge:
    def __init__(self, host: str = LAB4_HOST, port: int = LAB4_PORT) -> None:
        self.host = host
        self.port = port
        self.target = make_student()
        add_method_to_object(self.target, "introduce", introduce)
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.last_log: list[str] = []

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(8)
        self._sock.settimeout(0.5)
        self._thread = threading.Thread(target=self._loop, name="lab4-bridge", daemon=True)
        self._thread.start()
        logger.info("reflection bridge on %s:%s", self.host, self.port)

    def stop(self) -> None:
        self._stop.set()
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._thread = None
        self._sock = None

    def invoke(self, method: str, args: list[Any] | None = None) -> Any:
        func = getattr(self.target, method)
        return func(*(args or []))

    def _loop(self) -> None:
        assert self._sock is not None
        while not self._stop.is_set():
            try:
                client, _addr = self._sock.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            with client:
                try:
                    raw = client.recv(65536)
                    request = json.loads(raw.decode("utf-8"))
                    method = str(request["method"])
                    args = list(request.get("args") or [])
                    result = self.invoke(method, args)
                    reply = json.dumps({"ok": True, "result": result}, ensure_ascii=False)
                    self.last_log.append(f"{method}{tuple(args)} -> {result!r}")
                except Exception as exc:
                    reply = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
                client.sendall((reply + "\n").encode("utf-8"))


def send_request(method: str, args: list[Any] | None = None, host: str = LAB4_HOST, port: int = LAB4_PORT) -> dict:
    payload = json.dumps({"method": method, "args": args or []}, ensure_ascii=False).encode("utf-8")
    with socket.create_connection((host, port), timeout=3) as sock:
        sock.sendall(payload)
        data = sock.recv(65536)
    return json.loads(data.decode("utf-8"))
