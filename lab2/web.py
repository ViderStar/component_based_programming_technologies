"""HTML integration: a stdlib HTTP server whose /calc endpoint calls the COM object."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from configs.cfg import LAB2_WEB_HOST, LAB2_WEB_PORT
from lab2.calculator import Calculator
from lab2.client import ComError, Dispatch

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>COM calculator</title>
<style>
  body { font-family: -apple-system, Segoe UI, sans-serif; margin: 24px; color: #14202f; }
  h1 { font-size: 18px; color: #0055a5; }
  input, select, button { font-size: 15px; padding: 6px 8px; }
  input { width: 90px; }
  button { background: #0055a5; color: #fff; border: 0; border-radius: 4px; }
  #result { font-size: 22px; margin-top: 16px; }
  #meta { color: #5a687a; font-size: 12px; margin-top: 6px; }
</style>
<script>
  async function calculate() {
    const q = new URLSearchParams({
      op: document.getElementById('op').value,
      a: document.getElementById('a').value,
      b: document.getElementById('b').value,
    });
    const data = await (await fetch('/calc?' + q)).json();
    document.getElementById('result').innerText = data.error ? data.error : data.result;
    document.getElementById('meta').innerText = data.progid + '  ' + data.clsid;
  }
</script>
</head>
<body>
  <h1>Calculator served by a COM object</h1>
  <input id="a" value="2">
  <select id="op">
    <option value="Add">+</option>
    <option value="Sub">&minus;</option>
    <option value="Mul">&times;</option>
    <option value="Div">&divide;</option>
    <option value="Pow" selected>^</option>
  </select>
  <input id="b" value="10">
  <button onclick="calculate()">=</button>
  <p id="result"></p>
  <p id="meta"></p>
</body>
</html>
"""


def calculate(op: str, a: float, b: float) -> dict[str, object]:
    reply: dict[str, object] = {"progid": Calculator._reg_progid_, "clsid": Calculator._reg_clsid_}
    if op not in Calculator._public_methods_:
        return reply | {"error": f"Unknown operation: {op}"}
    try:
        com_object = Dispatch(Calculator._reg_progid_)
    except ComError as exc:
        return reply | {"error": str(exc)}
    try:
        return reply | {"result": getattr(com_object, op)(a, b)}
    except ComError as exc:
        return reply | {"error": str(exc)}
    finally:
        com_object.Release()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/":
            self._send(200, "text/html; charset=utf-8", PAGE.encode("utf-8"))
        elif url.path == "/calc":
            query = parse_qs(url.query)
            try:
                op, a, b = query["op"][0], float(query["a"][0]), float(query["b"][0])
            except (KeyError, ValueError) as exc:
                body = {"error": f"Bad request: {exc}"}
            else:
                body = calculate(op, a, b)
            self._send(200, "application/json", json.dumps(body).encode("utf-8"))
        else:
            self._send(404, "text/plain", b"not found")

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        pass


class WebServer:
    def __init__(self, host: str = LAB2_WEB_HOST, port: int = LAB2_WEB_PORT) -> None:
        self.host = host
        self.port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, name="lab2-web", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._server = None
        self._thread = None
