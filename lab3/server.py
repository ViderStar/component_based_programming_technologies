"""Static HTTP server for the Brython site.

The directory `lab3/` is the web root: the page lives in `/site/`, and `/numerics.py` is the very same
file the tests import, so Brython imports it with `pythonpath: ['/']`.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from configs.cfg import LAB3_WEB_HOST, LAB3_WEB_PORT

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
SITE_URL_PATH = "/site/index.html"


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".py": "text/x-python; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".html": "text/html; charset=utf-8",
    }

    def do_GET(self) -> None:
        if self.path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", SITE_URL_PATH)
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, *_args: object) -> None:
        pass


class SiteServer:
    def __init__(self, host: str = LAB3_WEB_HOST, port: int = LAB3_WEB_PORT) -> None:
        self.host = host
        self.port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}{SITE_URL_PATH}"

    def page(self, name: str = "index.html", query: str = "") -> str:
        return f"http://{self.host}:{self.port}/site/{name}{query}"

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._server = ThreadingHTTPServer((self.host, self.port), partial(Handler, directory=str(ROOT)))
        self._thread = threading.Thread(target=self._server.serve_forever, name="lab3-web", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._server = None
        self._thread = None


def main() -> None:
    server = SiteServer()
    server.start()
    print(f"Lab 3 site: {server.url}", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
