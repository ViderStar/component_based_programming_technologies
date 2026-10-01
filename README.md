# Component-Based Programming Technologies

## Course

BSUIR course on components: serialize an object, send it over the network, call a remote module, assemble a GUI, inspect a class at runtime.

Supervisor: **Oleg German**, PhD, Associate Professor, ITAS.

Student: **Artsem Lebiadzevich**, year-2 MSc, FCSN, POIT, PI, 2026.

### Topics

| Area | What is covered |
| --- | --- |
| **Serialization** | pickle, JSON, sockets, WebP as bytes and base64 |
| **COM** | registration, activation, `IDispatch`, Office and HTML clients |
| **Remote calls** (extra) | XML-RPC vs REST and CGI |
| **GUI components** (extra) | wxPython: toolbar, WebView, calendar, Office, PDF |
| **Reflection** (extra) | `type()`, `inspect`, runtime methods, Java→Python |

### Goals

1. Serialize a custom object and an image, restore them in another process and over TCP.
2. Publish a calculator as a COM server and call it from a GUI, Excel and a web page.
3. Extras: call a function in another process, build a desktop app from wx widgets, inspect and change a class at runtime.

---

## Lab theory

### [Lab 1: Serialization and deserialization](labs_info/lab1_theory.md)

**Focus**: pickle / JSON, files, TCP, GUI snapshot, WebP and base64.

**Keywords**: byte stream, `dump`/`load`, length-prefix, data URL.

---

### [Lab 2: COM server](labs_info/lab2_theory.md)

**Focus**: calculator COM class, registration, out-of-process activation, clients (wx keypad, Excel, HTML).

**Keywords**: ProgID, CLSID, LocalServer32, `IDispatch`, HRESULT.

---

### Lab 1 extras

Three more topics, kept next to Lab 1 in [`lab1/extras/`](lab1/extras/):

| Extra | Focus | Theory |
| --- | --- | --- |
| `rpc` | XML-RPC server, Python and Java clients | [theory](labs_info/lab1_extra_rpc_theory.md) |
| `wxui` | toolbar, browser, media, calendar, PDF, Word/Excel | [theory](labs_info/lab1_extra_wxui_theory.md) |
| `reflection` | dynamic `Student`, `inspect`, runtime methods, Java→Python bridge | [theory](labs_info/lab1_extra_reflection_theory.md) |

---

## How the labs connect

```
Lab 1: object ↔ bytes ↔ network
  ├──► extra rpc: bytes become a method call
  │      └──► extra reflection: method name is a string, resolved at runtime
  └──► Lab 2: the call goes to a registered component (COM)

extra wxui: GUI components used by every window
```

---

## Run

Python 3.12 is required (no wxPython wheels for 3.14 yet):

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
python scripts/make_assets.py
python main.py
```

| Command | Effect |
| --- | --- |
| `python main.py` | GUI launcher |
| `python main.py --lab 1` | CLI serialization + network |
| `python main.py --lab 1 --gui` | Lab 1 window only |
| `python main.py --lab 2` | CLI COM calculator: register, call, errors |
| `python main.py --lab 2 --gui` | Lab 2 window only |
| `python main.py --extra rpc` | XML-RPC add/mul/inspect (`--gui` for the window) |
| `python main.py --extra wxui` | wxPython toolbar window |
| `python main.py --extra reflection` | reflection + bridge (`--gui` for the window) |
| `python main.py --all` | all CLI demos |
| `python -m lab1.reader artifacts/student.json` | “other app” for Lab 1 |
| `python -m unittest tests.test_labs -v` | tests |

Each lab window has a **Cases** list: **Run** or **All** covers the assignment.

Handouts: [`docs/`](docs/), [`1OKT_2026/`](1OKT_2026/). Reports: [`reports/`](reports/) — PDF for [Lab 1](reports/lab1/lab1_report.pdf) and [Lab 2](reports/lab2/lab2_report.pdf).

## Sending an image (Lab 1)

- **pickle**: `Student.photo.data` is raw WebP bytes.
- **JSON**: `photo.data` is base64 plus `mime` and `filename`. Data URLs `data:image/webp;base64,...` are accepted.
- **Network**: 4-byte big-endian length + 8-byte format name + payload. Avoids the handout’s `recv(1024)` truncation.
