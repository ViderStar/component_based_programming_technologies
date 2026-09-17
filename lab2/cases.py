"""Checkable XML-RPC scenarios."""

from __future__ import annotations

import subprocess

from configs.cfg import LAB2_HOST, LAB2_PORT, PROJECT_ROOT
from lab2.rpc_client import call, make_proxy
from lab2.rpc_server import RpcServer

_SERVER: RpcServer | None = None
JAVA_SRC = PROJECT_ROOT / "lab2" / "java" / "XmlRpcClient.java"


def ensure_server() -> RpcServer:
    global _SERVER
    if _SERVER is None or not _SERVER.running:
        _SERVER = RpcServer()
        _SERVER.start()
    return _SERVER


def stop_server() -> None:
    global _SERVER
    if _SERVER is not None:
        _SERVER.stop()
        _SERVER = None


def add() -> str:
    ensure_server()
    result = call("add", 2, 3)
    if result != 5:
        raise AssertionError(result)
    return "add(2,3)=5"


def mul() -> str:
    ensure_server()
    result = call("mul", 6, 7)
    if result != 42:
        raise AssertionError(result)
    return "mul(6,7)=42"


def greet() -> str:
    ensure_server()
    result = str(call("greet_student"))
    if "Hello" not in result:
        raise AssertionError(result)
    return result


def inspect() -> str:
    ensure_server()
    members = call("inspect_module")
    if "add" not in members or "mul" not in members:
        raise AssertionError(members)
    listed = make_proxy().system.listMethods()
    if "add" not in listed:
        raise AssertionError(listed)
    return f"{len(listed)} methods"


def java_client() -> str:
    ensure_server()
    if subprocess.run(["which", "javac"], capture_output=True).returncode != 0:
        raise RuntimeError("javac not found")
    work = JAVA_SRC.parent
    compiled = subprocess.run(["javac", str(JAVA_SRC)], cwd=work, capture_output=True, text=True)
    if compiled.returncode != 0:
        raise RuntimeError(compiled.stderr.strip() or "javac failed")
    ran = subprocess.run(
        ["java", "-cp", str(work), "XmlRpcClient", LAB2_HOST, str(LAB2_PORT), "add", "5", "3"],
        capture_output=True,
        text=True,
    )
    if ran.returncode != 0:
        raise RuntimeError(ran.stderr or ran.stdout)
    if "8" not in ran.stdout:
        raise AssertionError(ran.stdout)
    return "Java POST add(5,3)=8"
