"""Out-of-process COM server: `python -m lab2.localserver {CLSID}` (the LocalServer32 command).

Serves one client over a loopback socket with an IDispatch-shaped protocol
(GetIDsOfNames, Invoke, Release) and exits when the client releases the object.
"""

from __future__ import annotations

import importlib
import json
import socket
import sys

from lab2 import registry

S_OK = 0
CO_E_CLASSSTRING = 0x800401F3
CO_E_SERVER_EXEC_FAILURE = 0x80080005
DISP_E_MEMBERNOTFOUND = 0x80020003
DISP_E_UNKNOWNNAME = 0x80020006
DISP_E_EXCEPTION = 0x80020009

HRESULT_NAMES = {
    CO_E_CLASSSTRING: "CO_E_CLASSSTRING",
    CO_E_SERVER_EXEC_FAILURE: "CO_E_SERVER_EXEC_FAILURE",
    DISP_E_MEMBERNOTFOUND: "DISP_E_MEMBERNOTFOUND",
    DISP_E_UNKNOWNNAME: "DISP_E_UNKNOWNNAME",
    DISP_E_EXCEPTION: "DISP_E_EXCEPTION",
}


def create_instance(clsid: str) -> object:
    spec = registry.query(rf"HKCR\CLSID\{clsid}\PythonCOM")
    if spec is None:
        raise LookupError(f"CLSID {clsid} is not registered")
    module_name, class_name = spec.rsplit(".", 1)
    return getattr(importlib.import_module(module_name), class_name)()


def handle(target: object, request: dict) -> dict:
    """Only `_public_methods_` are visible; DISPID is the 1-based position in that list."""
    public = list(target._public_methods_)
    op = request.get("op")
    if op == "GetIDsOfNames":
        name = request["name"]
        if name not in public:
            return {"hr": DISP_E_UNKNOWNNAME, "error": f"Unknown name: {name}"}
        return {"hr": S_OK, "dispid": public.index(name) + 1}
    if op == "Invoke":
        dispid = request["dispid"]
        if not 1 <= dispid <= len(public):
            return {"hr": DISP_E_MEMBERNOTFOUND, "error": f"Member not found: {dispid}"}
        try:
            result = getattr(target, public[dispid - 1])(*request.get("args", []))
        except Exception as exc:
            return {"hr": DISP_E_EXCEPTION, "error": str(exc)}
        return {"hr": S_OK, "result": result}
    return {"hr": DISP_E_MEMBERNOTFOUND, "error": f"Unknown operation: {op}"}


def serve(clsid: str) -> None:
    target = create_instance(clsid)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(10)
        print(listener.getsockname()[1], flush=True)
        client, _addr = listener.accept()
    with client, client.makefile("rw", encoding="utf-8") as stream:
        for line in stream:
            request = json.loads(line)
            if request.get("op") == "Release":
                break
            stream.write(json.dumps(handle(target, request)) + "\n")
            stream.flush()


if __name__ == "__main__":
    serve(sys.argv[1])
