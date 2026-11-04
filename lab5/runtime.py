"""Finding Tomcat, building `lab5.war` with javac and jar, and running Tomcat with its own CATALINA_BASE."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from configs.cfg import ARTIFACTS_DIR, LAB5_WEB_HOST, LAB5_WEB_PORT, PROJECT_ROOT, TOOLS_DIR
from lab4.runtime import find_tool

APP = "lab5"
SOURCES = PROJECT_ROOT / "lab5" / "java"
WEBAPP = PROJECT_ROOT / "lab5" / "webapp"
WORK_DIR = ARTIFACTS_DIR / "tomcat"
BASE = WORK_DIR / "base"  # CATALINA_BASE: conf, logs, webapps of this lab; CATALINA_HOME stays untouched
WAR = WORK_DIR / f"{APP}.war"
# Tomcat 9 from scripts/fetch_runtimes.py first; 8.5.5 of the handout starts on JDK 17,
# but its ecj 4.5.1 fails on JSPs that touch some JDK classes (java.lang.System)
_HOMES = ("tools/apache-tomcat-*", "task8/apache-tomcat-*")

SERVER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Server port="-1" shutdown="SHUTDOWN">
  <Service name="Catalina">
    <Connector port="{port}" address="{host}" protocol="HTTP/1.1" connectionTimeout="20000" URIEncoding="UTF-8" />
    <Engine name="Catalina" defaultHost="localhost">
      <Host name="localhost" appBase="webapps" unpackWARs="true" autoDeploy="true" />
    </Engine>
  </Service>
</Server>
"""


class TomcatUnavailable(RuntimeError):
    """Java, javac or Tomcat is missing; the message says how to get it."""


def find_home() -> Path | None:
    override = os.environ.get("CATALINA_HOME") or os.environ.get("TOMCAT_HOME")
    candidates = [Path(override)] if override else []
    for pattern in _HOMES:
        candidates.extend(sorted(PROJECT_ROOT.glob(pattern), reverse=True))
    for home in candidates:
        if (home / "bin" / "bootstrap.jar").is_file() and (home / "lib" / "servlet-api.jar").is_file():
            return home
    return None


def require() -> tuple[Path, Path]:
    java = find_tool("java")
    if java is None:
        raise TomcatUnavailable("Java not found: install a JDK (for example Temurin 17) or set JAVA_HOME")
    home = find_home()
    if home is None:
        raise TomcatUnavailable("Tomcat not found: set CATALINA_HOME or run `python scripts/fetch_runtimes.py`")
    return java, home


def available() -> bool:
    try:
        require()
    except TomcatUnavailable:
        return False
    return True


def server_info(home: Path) -> str:
    """`Apache Tomcat/8.5.5` from ServerInfo.properties inside catalina.jar."""
    with zipfile.ZipFile(home / "lib" / "catalina.jar") as jar:
        text = jar.read("org/apache/catalina/util/ServerInfo.properties").decode("utf-8")
    for line in text.splitlines():
        if line.startswith("server.info="):
            return line.split("=", 1)[1].strip()
    return "Apache Tomcat"


def build_war() -> Path:
    """javac the beans into WEB-INF/classes and pack the web application with `jar -cvf lab5.war`."""
    _java, home = require()
    javac, jar_tool = find_tool("javac"), find_tool("jar")
    if javac is None or jar_tool is None:
        raise TomcatUnavailable("javac/jar not found: a JDK (not only a JRE) is needed")
    stage = WORK_DIR / "stage"
    shutil.rmtree(stage, ignore_errors=True)
    shutil.copytree(WEBAPP, stage)
    classes = stage / "WEB-INF" / "classes"
    classes.mkdir(parents=True, exist_ok=True)
    sources = sorted(str(path) for path in SOURCES.rglob("*.java"))
    done = subprocess.run(
        [str(javac), "--release", "8", "-encoding", "UTF-8", "-cp", str(home / "lib" / "servlet-api.jar"), "-d", str(classes), *sources],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        raise RuntimeError(done.stderr[-800:])
    WAR.unlink(missing_ok=True)
    subprocess.run([str(jar_tool), "-cf", str(WAR), "-C", str(stage), "."], check=True, capture_output=True)
    return WAR


def _prepare_base(home: Path, host: str, port: int) -> None:
    for name in ("conf", "logs", "temp", "webapps", "work"):
        (BASE / name).mkdir(parents=True, exist_ok=True)
    (BASE / "conf" / "server.xml").write_text(SERVER_XML.format(host=host, port=port), encoding="utf-8")
    for name in ("web.xml", "logging.properties"):  # the default servlet, the JSP servlet and MIME types
        shutil.copyfile(home / "conf" / name, BASE / "conf" / name)
    # a fresh deployment: the old unpacked directory and compiled JSPs would hide changes
    shutil.rmtree(BASE / "webapps" / APP, ignore_errors=True)
    shutil.rmtree(BASE / "work", ignore_errors=True)
    shutil.copyfile(build_war(), BASE / "webapps" / WAR.name)


class Tomcat:
    """`java ... org.apache.catalina.startup.Bootstrap start` in a child process."""

    def __init__(self, host: str = LAB5_WEB_HOST, port: int = LAB5_WEB_PORT) -> None:
        self.host = host
        self.port = port
        self._process: subprocess.Popen | None = None

    @property
    def url(self) -> str:
        return self.page()

    def page(self, name: str = "", query: str = "") -> str:
        return f"http://{self.host}:{self.port}/{APP}/{name}{query}"

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def command(self) -> list[str]:
        java, home = require()
        return [
            str(java),
            "-Djava.awt.headless=true",  # ImageServlet.jsp draws with AWT; no Dock icon, works without a screen
            "-Dfile.encoding=UTF-8",
            f"-Dcatalina.home={home}",
            f"-Dcatalina.base={BASE}",
            f"-Djava.io.tmpdir={BASE / 'temp'}",
            "-Djava.util.logging.manager=org.apache.juli.ClassLoaderLogManager",
            f"-Djava.util.logging.config.file={BASE / 'conf' / 'logging.properties'}",
            "-cp",
            os.pathsep.join([str(home / "bin" / "bootstrap.jar"), str(home / "bin" / "tomcat-juli.jar")]),
            "org.apache.catalina.startup.Bootstrap",
            "start",
        ]

    def start(self, timeout: float = 60) -> None:
        if self.running:
            return
        _java, home = require()
        _prepare_base(home, self.host, self.port)
        log = open(BASE / "logs" / "console.log", "w", encoding="utf-8")
        self._process = subprocess.Popen(self.command(), stdout=log, stderr=subprocess.STDOUT, cwd=BASE)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise RuntimeError(f"Tomcat exited with {self._process.returncode}:\n{self.log_tail()}")
            try:
                with urllib.request.urlopen(self.page(), timeout=5) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, OSError):
                pass
            time.sleep(0.3)
        self.stop()
        raise TimeoutError(f"Tomcat did not answer on {self.url}:\n{self.log_tail()}")

    def stop(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

    @staticmethod
    def log_tail(lines: int = 15) -> str:
        path = BASE / "logs" / "console.log"
        if not path.exists():
            return ""
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])
