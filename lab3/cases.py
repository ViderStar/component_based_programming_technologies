"""Checkable Brython scenarios: the site, the three numerical tasks and the page running in a real browser."""

from __future__ import annotations

import html
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from lab3 import numerics
from lab3.server import SITE, SiteServer

SITE_FILES = ("index.html", "examples.html", "app.py", "brython.js", "brython_stdlib.js")
CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)

_SERVER: SiteServer | None = None


def ensure_server() -> SiteServer:
    global _SERVER
    if _SERVER is None or not _SERVER.running:
        _SERVER = SiteServer()
        _SERVER.start()
    return _SERVER


def stop_server() -> None:
    global _SERVER
    if _SERVER is not None:
        _SERVER.stop()
        _SERVER = None


def find_browser() -> str | None:
    """A Chromium-based browser that can dump the DOM of a page headlessly."""
    override = os.environ.get("CHROME")
    if override and Path(override).exists():
        return override
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found
    return None


def dump_dom(url: str, timeout: int = 90) -> str:
    """Load the page in headless Chrome, wait for Brython to finish and return the resulting DOM."""
    browser = find_browser()
    if browser is None:
        raise FileNotFoundError("no Chrome, Edge or Chromium found (set CHROME=/path/to/browser)")
    with tempfile.TemporaryDirectory() as profile:
        done = subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                f"--user-data-dir={profile}",
                "--virtual-time-budget=20000",
                "--dump-dom",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    if done.returncode != 0 or not done.stdout.strip():
        raise RuntimeError(f"browser exited with {done.returncode}: {done.stderr[-300:]}")
    return done.stdout


def _close(a: float, b: float, tol: float = 1e-6) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


# ---------------------------------------------------------------- cases


def site_files() -> str:
    missing = [name for name in SITE_FILES if not (SITE / name).exists()]
    if missing:
        raise FileNotFoundError(f"{', '.join(missing)} missing: run `python scripts/fetch_runtimes.py`")
    server = ensure_server()
    sizes = []
    for path in ("site/index.html", "site/app.py", "site/brython.js", "numerics.py"):
        with urllib.request.urlopen(f"http://{server.host}:{server.port}/{path}", timeout=10) as response:
            body = response.read()
        if not body:
            raise AssertionError(path)
        sizes.append(f"{path.split('/')[-1]} {len(body) // 1024 or 1} KiB")
    return ", ".join(sizes)


def polynomial_roots() -> str:
    expected = {
        (1, -6, 11, -6): [1, 2, 3],
        (1, 0, 1): [-1j, 1j],
        (1, 0, 0, 0, -1): [-1, -1j, 1j, 1],
        (2, 0, -8, 0, 0): [-2, 0, 0, 2],
        (1, -1, 1, -1, 1, -1): None,  # x^5 - x^4 + ... : only the residual is checked
    }
    worst = 0.0
    for coeffs, roots in expected.items():
        found = numerics.poly_roots(list(coeffs))
        if len(found) != len(coeffs) - 1:
            raise AssertionError(f"{coeffs}: {len(found)} roots")
        residual = max(abs(numerics.poly_eval([float(c) for c in coeffs], r)) for r in found)
        worst = max(worst, residual)
        if residual > 1e-9:
            raise AssertionError(f"{coeffs}: residual {residual}")
        if roots is not None and any(abs(a - b) > 1e-8 for a, b in zip(found, roots)):
            raise AssertionError(f"{coeffs}: {found} != {roots}")
    try:
        numerics.poly_roots([5])
    except ValueError:
        pass
    else:
        raise AssertionError("a constant has no roots")
    return f"5 polynomials, max |p(root)| = {worst:.1e}; x^2+1 -> ±i"


def regression() -> str:
    xs = [float(x) for x in range(1, 9)]
    model = numerics.linear_regression(xs, [3 * x - 2 for x in xs])
    if not (_close(model["slope"], 3) and _close(model["intercept"], -2) and _close(model["r2"], 1)):
        raise AssertionError(model)
    ahead = numerics.forecast(model, xs, 2)
    if not (_close(ahead[0][1], 25) and _close(ahead[1][1], 28)):
        raise AssertionError(ahead)

    xs, ys = numerics.parse_points(numerics.DEMO_SERIES)  # the stdlib is an independent reference
    reference = statistics.linear_regression(xs, ys)
    model = numerics.linear_regression(xs, ys)
    if not (_close(model["slope"], reference.slope) and _close(model["intercept"], reference.intercept)):
        raise AssertionError((model, reference))
    if not _close(model["r2"], statistics.correlation(xs, ys) ** 2):
        raise AssertionError(model["r2"])
    return f"y = {model['slope']:.5g}x + {model['intercept']:.5g}, R² = {model['r2']:.4f}, x=11 -> {numerics.predict(model, 11):.2f}"


def optimum() -> str:
    quad = numerics.minimize("(x - 1)^2 + 2*(y + 2)^2 + x*y", [0.0, 0.0])
    if not (_close(quad["x"][0], 16 / 7, 1e-5) and _close(quad["x"][1], -18 / 7, 1e-5)):
        raise AssertionError(quad)
    rosen = numerics.minimize("(1 - x)^2 + 100*(y - x^2)^2", [-1.2, 1.0])
    if not (_close(rosen["x"][0], 1, 1e-5) and _close(rosen["x"][1], 1, 1e-5)):
        raise AssertionError(rosen)
    descent = numerics.minimize("(x - 1)^2 + 2*(y + 2)^2 + x*y", [0.0, 0.0], "gradient")
    if not (_close(descent["x"][0], 16 / 7, 1e-5) and descent["converged"]):
        raise AssertionError(descent)
    golden = numerics.minimize("x^4 - 3*x^2 + x", [0.0], "golden", bracket=(-0.5, 2.0))
    local = golden["x"][0]
    if abs(4 * local**3 - 6 * local + 1) > 1e-6:  # f'(x) = 0 at a minimum
        raise AssertionError(golden)
    top = numerics.minimize("sin(x)*exp(-0.1*x)", [1.0], maximize=True)
    if top["kind"] != "maximum" or not _close(top["x"][0], math.atan(10), 1e-4):
        raise AssertionError(top)
    try:
        numerics.minimize("__import__('os').getcwd()", [1.0, 1.0])
    except ValueError:
        pass
    else:
        raise AssertionError("names outside the math set must be refused")
    return (
        f"bowl -> ({quad['x'][0]:.4f}, {quad['x'][1]:.4f}), Rosenbrock -> ({rosen['x'][0]:.4f}, {rosen['x'][1]:.4f}) "
        f"in {rosen['iterations']} steps, max of sin·exp at x = {top['x'][0]:.4f}"
    )


def brython_page() -> str:
    """The real thing: Brython compiles app.py in a browser; its numbers must match CPython's."""
    if find_browser() is None:
        return "skipped: no Chromium-based browser"
    server = ensure_server()
    dom = dump_dom(server.page(query="?autorun=1"))
    match = re.search(r'<pre id="dump"[^>]*>(.*?)</pre>', dom, re.S)
    if not match or not match.group(1).strip():
        raise AssertionError("Brython did not finish: the dump is empty")
    from_browser = json.loads(html.unescape(match.group(1)))
    expected = json.loads(json.dumps(numerics.demo_report()))
    checked = 0
    for got, want in zip(from_browser["polynomials"], expected["polynomials"]):
        if got["text"] != want["text"] or len(got["roots"]) != len(want["roots"]):
            raise AssertionError((got, want))
        for (gr, gi), (wr, wi) in zip(got["roots"], want["roots"]):
            if abs(gr - wr) > 1e-6 or abs(gi - wi) > 1e-6:
                raise AssertionError((got["text"], gr, gi, wr, wi))
            checked += 1
    for key in ("slope", "intercept", "r2"):
        if not _close(from_browser["regression"][key], expected["regression"][key]):
            raise AssertionError(key)
        checked += 1
    for got, want in zip(from_browser["optima"], expected["optima"]):
        if any(abs(a - b) > 1e-4 for a, b in zip(got["x"], want["x"])) or abs(got["fx"] - want["fx"]) > 1e-6:
            raise AssertionError((got, want))
        checked += 1
    version = re.search(r"Brython (\d+\.\d+\.\d+)", dom)
    if "roots_result" not in dom or "p(x) = x^3 - 6x^2 + 11x - 6" not in dom:
        raise AssertionError("the roots table was not drawn")
    return f"Brython {version.group(1) if version else '?'} in headless browser: {checked} values equal CPython's"


def handout_examples() -> str:
    if find_browser() is None:
        return "skipped: no Chromium-based browser"
    dom = dump_dom(ensure_server().page("examples.html"))
    # the text is also in the script source, so look for the element that only Brython can create
    if "<h2>Oleg German, are this you?</h2>" not in dom:
        raise AssertionError("the H2 created from Python is not in the page")
    return '<h2>Oleg German, are this you?</h2> was created by browser.html.H2 and is in the DOM'
