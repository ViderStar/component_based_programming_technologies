# Lab 2: COM server

## Idea

COM (Component Object Model) lets a client written in one language call an object written in another. The client never imports the class: it asks the system for an object by name, and the system finds the server, starts it and hands back an interface pointer.

## Terms

| Term | Meaning |
| --- | --- |
| **COM object** | instance of a COM class behind one or more interfaces |
| **Interface** | the methods a client may call; scripting clients use `IDispatch` |
| **CLSID** | GUID of the class, e.g. `{7C1B9A52-3E64-4F0A-9D21-5B8E0C6A2F14}` |
| **ProgID** | readable name of the class, `Lab2.Calculator` |
| **LocalServer32** | command that starts an out-of-process (EXE) server |

## How a call travels

1. **Registration** writes `HKEY_CLASSES_ROOT\<ProgID>\CLSID` and `HKEY_CLASSES_ROOT\CLSID\{...}\LocalServer32`.
2. **Activation**: `Dispatch("Lab2.Calculator")` reads ProgID → CLSID → LocalServer32 and starts the server process.
3. **Call**: `IDispatch::GetIDsOfNames("Add")` returns a DISPID, then `IDispatch::Invoke(dispid, args)` runs the method in the server.
4. **Release**: when the last reference goes away the server exits.

## The COM class

`lab2/calculator.py` follows the pywin32 conventions from the handout:

```python
class Calculator:
    _reg_progid_ = "Lab2.Calculator"
    _reg_clsid_ = "{7C1B9A52-3E64-4F0A-9D21-5B8E0C6A2F14}"
    _reg_clsctx_ = CLSCTX_LOCAL_SERVER
    _public_methods_ = ["Add", "Sub", "Mul", "Div", "Pow"]
```

Only `_public_methods_` are visible to clients. `Calculator.secret()` exists in Python but a COM client gets `DISP_E_UNKNOWNNAME`.

## Two runtimes for one class

| | Windows | macOS / Linux (this repo's GUI) |
| --- | --- | --- |
| Registry | `HKEY_CLASSES_ROOT` | `artifacts/registry.json` with the same keys |
| Register | `python lab2\windows\calc_com_server.py --register` (pywin32) | `lab2.registry.register(Calculator)` |
| Server process | `pythonw -m win32com.server.localserver {CLSID}` | `python -m lab2.localserver {CLSID}` |
| Client | `win32com.client.Dispatch`, VBA `CreateObject` | `lab2.client.Dispatch` |
| Transport | COM runtime (RPC) | JSON lines over a loopback socket |

COM is a Windows technology and pywin32 does not install on macOS. `lab2/registry.py`, `lab2/localserver.py` and `lab2/client.py` reproduce the mechanism (registry lookup, out-of-process activation, late binding by DISPID, HRESULT errors) so the lab runs anywhere. It is a model of COM, not COM: no real `IUnknown`, no marshalling of interface pointers, no type libraries.

## Errors

| HRESULT | When |
| --- | --- |
| `CO_E_CLASSSTRING 0x800401F3` | ProgID is not registered |
| `DISP_E_UNKNOWNNAME 0x80020006` | method is not in `_public_methods_` |
| `DISP_E_EXCEPTION 0x80020009` | the method raised (division by zero) |

## Clients

- **Calculator keypad** (wx): every `=` is a COM call.
- **Excel / Word**: `lab2/windows/CalculatorClient.bas` uses `CreateObject("Lab2.Calculator")`. Office for Mac has no `CreateObject` for custom COM servers, so on macOS a Python client fills `artifacts/com_calculator.csv` from the COM object and opens it in Excel.
- **HTML**: `lab2/web.py` (stdlib `http.server`, same role as Flask in the handout) serves a page; `/calc?op=Pow&a=2&b=10` calls the COM object and returns JSON.

## Links

- **Lab 1** moves an object's bytes; COM moves a method call and keeps the object in the server.
- **XML-RPC extra** is the same remote-call idea over HTTP; COM adds a system registry and activation.
- **Reflection extra**: `GetIDsOfNames` + `Invoke` is call-by-name, like `getattr(obj, name)(*args)`.
