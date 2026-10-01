"""COM client side: `Dispatch(progid)` resolves ProgID -> CLSID -> LocalServer32 and returns a proxy."""

from __future__ import annotations

import json
import shlex
import socket
import subprocess
from collections.abc import Callable
from typing import Any

from configs.cfg import PROJECT_ROOT
from lab2 import registry
from lab2.localserver import CO_E_CLASSSTRING, CO_E_SERVER_EXEC_FAILURE, HRESULT_NAMES, S_OK

Trace = Callable[[str], None]


class ComError(Exception):
    def __init__(self, hresult: int, description: str) -> None:
        self.hresult = hresult
        self.name = HRESULT_NAMES.get(hresult, "E_FAIL")
        super().__init__(f"{self.name} 0x{hresult:08X}: {description}")


class DispatchProxy:
    """Late-bound proxy: every attribute is a GetIDsOfNames + Invoke round trip to the server process."""

    def __init__(self, progid: str, clsid: str, command: str, trace: Trace | None = None) -> None:
        self._progid = progid
        self._clsid = clsid
        self._trace = trace or (lambda _line: None)
        self._process = subprocess.Popen(
            shlex.split(command), cwd=PROJECT_ROOT, stdout=subprocess.PIPE, text=True
        )
        port = self._process.stdout.readline().strip()
        if not port:
            self._process.wait()
            raise ComError(CO_E_SERVER_EXEC_FAILURE, f"Server execution failed: {command}")
        self._sock = socket.create_connection(("127.0.0.1", int(port)), timeout=5)
        self._stream = self._sock.makefile("rw", encoding="utf-8")
        self._trace(f"CoCreateInstance {clsid} -> LocalServer32 pid {self._process.pid}, port {port}")

    @property
    def pid(self) -> int:
        return self._process.pid

    def _call(self, request: dict) -> dict:
        if self._stream is None:
            raise ComError(CO_E_SERVER_EXEC_FAILURE, "Object was released")
        self._stream.write(json.dumps(request) + "\n")
        self._stream.flush()
        line = self._stream.readline()
        if not line:
            raise ComError(CO_E_SERVER_EXEC_FAILURE, "Server process is gone")
        reply = json.loads(line)
        if reply["hr"] != S_OK:
            error = ComError(reply["hr"], reply["error"])
            self._trace(f"  -> {error}")
            raise error
        return reply

    def __getattr__(self, name: str) -> Callable[..., Any]:
        if name.startswith("_"):
            raise AttributeError(name)

        def method(*args: Any) -> Any:
            self._trace(f'GetIDsOfNames("{name}")')
            dispid = self._call({"op": "GetIDsOfNames", "name": name})["dispid"]
            self._trace(f"  -> DISPID {dispid}")
            self._trace(f"Invoke({dispid}, {list(args)})")
            result = self._call({"op": "Invoke", "dispid": dispid, "args": list(args)})["result"]
            self._trace(f"  -> {result!r}")
            return result

        return method

    def Release(self) -> None:
        if self._stream is None:
            return
        try:
            self._stream.write(json.dumps({"op": "Release"}) + "\n")
            self._stream.flush()
        except OSError:
            pass
        self._stream.close()
        self._sock.close()
        self._stream = None
        self._process.wait(timeout=5)
        self._process.stdout.close()
        self._trace(f"Release -> server pid {self._process.pid} exited")

    def __del__(self) -> None:
        if getattr(self, "_stream", None) is not None:
            self.Release()


def Dispatch(progid: str, trace: Trace | None = None) -> DispatchProxy:
    clsid = registry.query(rf"HKCR\{progid}\CLSID")
    if clsid is None:
        raise ComError(CO_E_CLASSSTRING, f"Invalid class string: {progid} (ProgID is not registered)")
    command = registry.query(rf"HKCR\CLSID\{clsid}\LocalServer32")
    if command is None:
        raise ComError(CO_E_CLASSSTRING, f"No LocalServer32 for {clsid}")
    return DispatchProxy(progid, clsid, command, trace)
