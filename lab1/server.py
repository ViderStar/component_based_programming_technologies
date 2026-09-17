"""TCP server that deserializes Student (pickle or JSON) and echoes it back."""

from __future__ import annotations

import logging
import socket
import threading
from typing import Callable

from configs.cfg import LAB1_HOST, LAB1_PORT
from lab1.codecs import loads_json_student, loads_pickle
from lab1.models import Student
from lab1.net import pack_envelope, recv_message, send_message, unpack_envelope

logger = logging.getLogger(__name__)


def decode_student(fmt: str, payload: bytes) -> Student:
    if fmt == "pickle":
        obj = loads_pickle(payload)
        if not isinstance(obj, Student):
            raise TypeError(f"expected Student, got {type(obj)!r}")
        return obj
    if fmt == "json":
        return loads_json_student(payload)
    raise ValueError(f"unknown format: {fmt}")


class StudentServer:
    def __init__(
        self,
        host: str = LAB1_HOST,
        port: int = LAB1_PORT,
        on_student: Callable[[Student, str], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.on_student = on_student
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.last_student: Student | None = None

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
        self._thread = threading.Thread(target=self._loop, name="lab1-server", daemon=True)
        self._thread.start()
        logger.info("Lab1 server listening on %s:%s", self.host, self.port)

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

    def _loop(self) -> None:
        assert self._sock is not None
        while not self._stop.is_set():
            try:
                client, addr = self._sock.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            logger.info("client %s", addr)
            try:
                self._handle(client)
            except Exception:
                logger.exception("client handler failed")
            finally:
                client.close()

    def _handle(self, client: socket.socket) -> None:
        blob = recv_message(client)
        fmt, payload = unpack_envelope(blob)
        student = decode_student(fmt, payload)
        self.last_student = student
        if self.on_student:
            self.on_student(student, fmt)
        send_message(client, pack_envelope(fmt, payload))
