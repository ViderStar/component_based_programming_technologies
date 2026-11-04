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
| **Python in the browser** | Brython: DOM from Python, numerical methods on a web page |
| **Python on the JVM** | Jython: Java classes from Python, Swing menu application |
| **Server pages** | JSP on Tomcat: JavaBeans, rates, an image, a translator, a site |
| **Remote calls** (extra) | XML-RPC vs REST and CGI |
| **GUI components** (extra) | wxPython: toolbar, WebView, calendar, Office, PDF |
| **Reflection** (extra) | `type()`, `inspect`, runtime methods, Java→Python |

### Goals

1. Serialize a custom object and an image, restore them in another process and over TCP.
2. Publish a calculator as a COM server and call it from a GUI, Excel and a web page.
3. Write a client site in Python (Brython): polynomial roots, linear-regression forecast, optimum of a function.
4. Mix Java and Python (Jython): use Java classes from Python, and draw two pictures and a sine wave from a Swing menu.
5. Write JSP pages on Tomcat: dollar and euro rates, a PNG drawn by a page, an English ⇄ Russian translator, a site sent through `PrintWriter`.
5. Extras: call a function in another process, build a desktop app from wx widgets, inspect and change a class at runtime.

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

### [Lab 3: Brython](labs_info/lab3_theory.md)

**Focus**: Python scripts in an HTML page, DOM events, a canvas, the same numerical module in the browser and in CPython.

**Keywords**: `brython()`, `browser.document`, `bind`, `pythonpath`.

---

### [Lab 4: Jython](labs_info/lab4_theory.md)

**Focus**: Java ⇄ Python on the JVM, a Python subclass of a Java class, Swing menu, `paintComponent`, `PythonInterpreter`.

**Keywords**: `jython-standalone.jar`, `sys.path.append(jar)`, `JFrame`, `JMenuBar`, `Graphics2D`.

---

### [Lab 5: JSP](labs_info/lab5_theory.md)

**Focus**: JSP pages and JavaBeans on Tomcat, a war built with `javac` and `jar`, HTML and PNG answers.

**Keywords**: `<%! %>`, `<%= %>`, `jsp:useBean`, `scope="session"`, `ImageIO.write`, `response.getWriter()`.

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
python scripts/fetch_runtimes.py   # Brython for Lab 3, Jython jar for Lab 4, Tomcat 9 for Lab 5 (needs a JDK, e.g. Temurin 17)
python main.py
```

| Command | Effect |
| --- | --- |
| `python main.py` | GUI launcher |
| `python main.py --lab 1` | CLI serialization + network |
| `python main.py --lab 1 --gui` | Lab 1 window only |
| `python main.py --lab 2` | CLI COM calculator: register, call, errors |
| `python main.py --lab 2 --gui` | Lab 2 window only |
| `python main.py --lab 3` | CLI Brython: numerics, site, the page in a headless browser |
| `python main.py --lab 3 --gui` | Lab 3 window: the site in a web view |
| `python main.py --lab 4` | CLI Jython: Java ⇄ Python examples, menu application checks |
| `python main.py --lab 4 --gui` | Lab 4 window: preview, buttons for the Swing windows |
| `python main.py --lab 5` | CLI JSP: build `lab5.war`, start Tomcat, check every page |
| `python main.py --lab 5 --gui` | Lab 5 window: the JSP application in a web view |
| `python -m lab3.server` | serve the Brython site at `http://127.0.0.1:8030/` |
| `python -m lab5.server` | run Tomcat with Lab 5 at `http://127.0.0.1:8040/lab5/` |
| `python main.py --extra rpc` | XML-RPC add/mul/inspect (`--gui` for the window) |
| `python main.py --extra wxui` | wxPython toolbar window |
| `python main.py --extra reflection` | reflection + bridge (`--gui` for the window) |
| `python main.py --all` | all CLI demos |
| `python -m lab1.reader artifacts/student.json` | “other app” for Lab 1 |
| `python -m unittest tests.test_labs -v` | tests |

Each lab window has a **Cases** list: **Run** or **All** covers the assignment.

Handouts: [`docs/`](docs/), [`1OKT_2026/`](1OKT_2026/), [`Lab_Brython/`](Lab_Brython/), [`Lab_Jython/`](Lab_Jython/), [`task8/`](task8/). Reports: [`reports/`](reports/) — PDF for [Lab 1](reports/lab1/lab1_report.pdf), [Lab 2](reports/lab2/lab2_report.pdf), [Lab 3](reports/lab3/lab3_report.pdf), [Lab 4](reports/lab4/lab4_report.pdf) and [Lab 5](reports/lab5/lab5_report.pdf).

Lab 4 runs the Jython scripts with `java -jar tools/jython-standalone-2.7.3.jar`; Java is looked up in `JAVA_HOME`, `/Library/Java/JavaVirtualMachines` and `PATH` (override the jar with `JYTHON_JAR`, the browser for Lab 3 with `CHROME`). Lab 5 uses `tools/apache-tomcat-9.0.122` (override with `CATALINA_HOME`); Tomcat 8.5.5 of the handout cannot compile JSPs on JDK 17. Without Java or the jar the Lab 4 cases are skipped; without a Chromium-based browser only the page-in-a-browser cases of Lab 3 are.

## Sending an image (Lab 1)

- **pickle**: `Student.photo.data` is raw WebP bytes.
- **JSON**: `photo.data` is base64 plus `mime` and `filename`. Data URLs `data:image/webp;base64,...` are accepted.
- **Network**: 4-byte big-endian length + 8-byte format name + payload. Avoids the handout’s `recv(1024)` truncation.
