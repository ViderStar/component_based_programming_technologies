"""Checkable COM scenarios: registration, activation, calls, errors, Excel and HTML clients."""

from __future__ import annotations

import csv
import json
import os
import urllib.request

from configs.cfg import ARTIFACTS_DIR
from helpers.paths import ensure_artifacts_dir
from lab2 import registry
from lab2.calculator import Calculator
from lab2.client import ComError, Dispatch, DispatchProxy, Trace
from lab2.web import WebServer

PROGID = Calculator._reg_progid_
CLSID = Calculator._reg_clsid_
SYMBOLS = {"Add": "+", "Sub": "-", "Mul": "*", "Div": "/", "Pow": "^"}
SAMPLES = [("Add", 2, 3, 5), ("Sub", 7, 10, -3), ("Mul", 6, 7, 42), ("Div", 7, 2, 3.5), ("Pow", 2, 10, 1024)]
EXCEL_CSV = ARTIFACTS_DIR / "com_calculator.csv"

_WEB: WebServer | None = None


def ensure_web() -> WebServer:
    global _WEB
    if _WEB is None or not _WEB.running:
        _WEB = WebServer()
        _WEB.start()
    return _WEB


def stop_web() -> None:
    global _WEB
    if _WEB is not None:
        _WEB.stop()
        _WEB = None


def connect(trace: Trace | None = None) -> DispatchProxy:
    ensure_artifacts_dir()
    registry.register(Calculator)
    return Dispatch(PROGID, trace)


def register() -> str:
    ensure_artifacts_dir()
    keys = registry.register(Calculator)
    if registry.query(rf"HKCR\{PROGID}\CLSID") != CLSID:
        raise AssertionError("ProgID does not point to the CLSID")
    return f"{PROGID} -> {CLSID}, {len(keys)} keys"


def registry_keys() -> str:
    register()
    command = registry.query(rf"HKCR\CLSID\{CLSID}\LocalServer32")
    if not command or "lab2.localserver" not in command:
        raise AssertionError(command)
    if registry.query(rf"HKCR\CLSID\{CLSID}\ProgID") != PROGID:
        raise AssertionError("CLSID does not point back to the ProgID")
    return "LocalServer32 -> python -m lab2.localserver"


def dispatch(trace: Trace | None = None) -> str:
    calc = connect(trace)
    try:
        if calc.pid == os.getpid():
            raise AssertionError("server must be a separate process")
        return f"out-of-process server pid {calc.pid}"
    finally:
        calc.Release()


def arithmetic(trace: Trace | None = None) -> str:
    calc = connect(trace)
    try:
        parts = []
        for method, a, b, expected in SAMPLES:
            result = getattr(calc, method)(a, b)
            if result != expected:
                raise AssertionError(f"{method}({a}, {b}) = {result}")
            parts.append(f"{a}{SYMBOLS[method]}{b}={result}")
        return "  ".join(parts)
    finally:
        calc.Release()


def com_errors(trace: Trace | None = None) -> str:
    calc = connect(trace)
    try:
        seen = []
        for call in (lambda: calc.Div(1, 0), lambda: calc.secret()):
            try:
                call()
            except ComError as exc:
                seen.append(exc.name)
            else:
                raise AssertionError("COM error expected")
        if seen != ["DISP_E_EXCEPTION", "DISP_E_UNKNOWNNAME"]:
            raise AssertionError(seen)
        return "1/0 -> DISP_E_EXCEPTION, secret -> DISP_E_UNKNOWNNAME"
    finally:
        calc.Release()


def excel_sheet(trace: Trace | None = None) -> str:
    """What the VBA macro does on Windows: fill a sheet with results taken from the COM object."""
    calc = connect(trace)
    try:
        rows = [(a, SYMBOLS[method], b, getattr(calc, method)(a, b), f"{PROGID}.{method}") for method, a, b, _ in SAMPLES]
    finally:
        calc.Release()
    with EXCEL_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["a", "op", "b", "result", "COM method"])
        writer.writerows(rows)
    return f"{EXCEL_CSV.name}, {len(rows)} rows"


def html_client() -> str:
    register()
    server = ensure_web()
    with urllib.request.urlopen(server.url, timeout=5) as response:
        if "COM object" not in response.read().decode("utf-8"):
            raise AssertionError("page")
    with urllib.request.urlopen(f"{server.url}calc?op=Pow&a=2&b=10", timeout=10) as response:
        reply = json.loads(response.read())
    if reply.get("result") != 1024 or reply.get("clsid") != CLSID:
        raise AssertionError(reply)
    return f"GET /calc?op=Pow&a=2&b=10 -> {reply['result']}"


def unregister() -> str:
    register()
    removed = registry.unregister(Calculator)
    try:
        Dispatch(PROGID)
    except ComError as exc:
        name = exc.name
    else:
        raise AssertionError("Dispatch must fail after unregister")
    finally:
        registry.register(Calculator)
    if name != "CO_E_CLASSSTRING":
        raise AssertionError(name)
    return f"{removed} keys removed, Dispatch -> {name}; registered again"
