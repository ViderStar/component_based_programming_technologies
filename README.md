# Component-Based Programming Technologies

## Course

BSUIR course on components: serialize an object, send it over the network, call a remote module, assemble a GUI, inspect a class at runtime.

Supervisor: **Oleg German**, PhD, Associate Professor, ITAS.

Student: **Artsem Lebiadzevich**, year-2 MSc, FCSN, POIT, PI, 2026.

### Topics

| Area | What is covered |
| --- | --- |
| **Serialization** | pickle, JSON, sockets, WebP as bytes and base64 |
| **Remote calls** | XML-RPC vs REST and CGI |
| **GUI components** | wxPython: toolbar, WebView, calendar, Office, PDF |
| **Reflection** | `type()`, `inspect`, runtime methods, Java→Python |

### Goals

1. Serialize a custom object and an image, restore them in another process and over TCP.
2. Call a function that lives in another process as if it were local.
3. Build a desktop app from stock and custom wx widgets.
4. Inspect and change a class at runtime.

---

## Lab theory

### [Lab 1: Serialization and deserialization](labs_info/lab1_theory.md)

**Focus**: pickle / JSON, files, TCP, GUI snapshot, WebP and base64.

**Keywords**: byte stream, `dump`/`load`, length-prefix, data URL.

---

### [Lab 2: Remote module invocation](labs_info/lab2_theory.md)

**Focus**: XML-RPC server and client, including a Java client with no extra libraries.

**Keywords**: RPC, SOAP/XML, REST, MQTT, CGI (theory only).

---

### [Lab 3: wxPython components](labs_info/lab3_theory.md)

**Focus**: toolbar with icons and tooltips, browser, media, calendar, PDF, Word/Excel.

**Keywords**: widget, sizer, event, custom component.

---

### [Lab 4: Reflection](labs_info/lab4_theory.md)

**Focus**: dynamic `Student`, `getattr`/`inspect`, runtime methods, Java→Python bridge.

**Keywords**: introspection, `type()`, `types.MethodType`, expected-output annotations.

---

## How the labs connect

```
Lab 1: object ↔ bytes ↔ network
  └──► Lab 2: bytes become a method call (RPC)
         └──► Lab 4: method name is a string, resolved via reflection

Lab 3: GUI components used by Labs 1–4
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
| `python main.py --lab 2` | XML-RPC add/mul/inspect |
| `python main.py --lab 3` | wxPython toolbar window |
| `python main.py --lab 4` | reflection + bridge |
| `python main.py --all` | all CLI demos |
| `python -m lab1.reader artifacts/student.json` | “other app” for Lab 1 |
| `python -m unittest tests.test_labs -v` | tests |

Each lab window has a **Cases** list: **Run** or **All** covers the assignment.

Handouts: [`docs/`](docs/). Reports: [`reports/`](reports/).

## Sending an image (Lab 1)

- **pickle**: `Student.photo.data` is raw WebP bytes.
- **JSON**: `photo.data` is base64 plus `mime` and `filename`. Data URLs `data:image/webp;base64,...` are accepted.
- **Network**: 4-byte big-endian length + 8-byte format name + payload. Avoids the handout’s `recv(1024)` truncation.
