#!/usr/bin/env python3
"""Prepare the runtimes for Lab 3 and Lab 4.

* Brython: `brython.js` and `brython_stdlib.js` are copied from the installed `brython` package into
  `lab3/site/`, so the page works without a CDN (the handout recommends a local installation).
* Jython: the standalone jar is downloaded from Maven Central into `tools/` and checked against the
  SHA-1 that Maven publishes next to it.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configs.cfg import TOOLS_DIR  # noqa: E402

JYTHON_VERSION = "2.7.3"
JYTHON_URL = f"https://repo1.maven.org/maven2/org/python/jython-standalone/{JYTHON_VERSION}/jython-standalone-{JYTHON_VERSION}.jar"
SITE = ROOT / "lab3" / "site"


def fetch_brython() -> None:
    import brython

    data = Path(brython.__file__).parent / "data"
    SITE.mkdir(parents=True, exist_ok=True)
    for name in ("brython.js", "brython_stdlib.js"):
        shutil.copyfile(data / name, SITE / name)
        print("brython ->", SITE / name)


def fetch_jython() -> None:
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    target = TOOLS_DIR / f"jython-standalone-{JYTHON_VERSION}.jar"
    with urllib.request.urlopen(JYTHON_URL + ".sha1", timeout=30) as response:
        expected = response.read().decode("ascii").split()[0]
    if target.exists() and hashlib.sha1(target.read_bytes()).hexdigest() == expected:
        print("jython up to date ->", target)
        return
    with urllib.request.urlopen(JYTHON_URL, timeout=300) as response:
        payload = response.read()
    actual = hashlib.sha1(payload).hexdigest()
    if actual != expected:
        raise SystemExit(f"SHA-1 mismatch for {JYTHON_URL}: {actual} != {expected}")
    target.write_bytes(payload)
    print(f"jython {JYTHON_VERSION} ({len(payload) // 1024} KiB, sha1 ok) ->", target)


def main() -> None:
    fetch_brython()
    fetch_jython()


if __name__ == "__main__":
    main()
