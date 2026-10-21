"""Finding Java and Jython and running Jython scripts, Java classes and jars from CPython."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from configs.cfg import ARTIFACTS_DIR, PROJECT_ROOT, TOOLS_DIR

JYTHON_VERSION = "2.7.3"
JYTHON_JAR = Path(os.environ.get("JYTHON_JAR", TOOLS_DIR / f"jython-standalone-{JYTHON_VERSION}.jar"))
SCRIPTS = PROJECT_ROOT / "lab4" / "jython"
JAVA_SOURCES = PROJECT_ROOT / "lab4" / "java"
WORK_DIR = ARTIFACTS_DIR / "jython"

_JAVA_ROOTS = ("/Library/Java/JavaVirtualMachines", "/usr/lib/jvm", "/opt/homebrew/opt")


class JythonUnavailable(RuntimeError):
    """Java or the Jython jar is missing; the message says how to get it."""


def _works(java: Path) -> bool:
    try:
        done = subprocess.run([str(java), "-version"], capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0


def _homes() -> list[Path]:
    homes = [Path(os.environ["JAVA_HOME"])] if os.environ.get("JAVA_HOME") else []
    for root in _JAVA_ROOTS:
        base = Path(root)
        if base.is_dir():
            homes.extend(sorted(base.glob("*/Contents/Home")) + sorted(base.glob("*")) + sorted(base.glob("*/libexec/openjdk.jdk/Contents/Home")))
    return homes


def find_tool(name: str = "java") -> Path | None:
    """`java`, `javac` or `jar` of a working JDK. The /usr/bin stub on macOS is skipped when no JDK is installed."""
    for home in _homes():
        candidate = home / "bin" / name
        if candidate.is_file() and (name != "java" or _works(candidate)):
            return candidate
    on_path = shutil.which(name)
    if on_path and (name != "java" or _works(Path(on_path))):
        return Path(on_path)
    return None


def require() -> tuple[Path, Path]:
    java = find_tool("java")
    if java is None:
        raise JythonUnavailable("Java not found: install a JDK (for example Temurin 17) or set JAVA_HOME")
    if not JYTHON_JAR.exists():
        raise JythonUnavailable(f"{JYTHON_JAR.name} not found: run `python scripts/fetch_runtimes.py`")
    return java, JYTHON_JAR


def available() -> bool:
    try:
        require()
    except JythonUnavailable:
        return False
    return True


def _base_command(java: Path, headless: bool, properties: dict[str, str] | None) -> list[str]:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    options = {
        "python.cachedir": str(WORK_DIR / "cache"),  # the package cache of Jython stays inside the project
        "file.encoding": "UTF-8",
        "python.console.encoding": "UTF-8",
        "java.awt.headless": "true" if headless else "false",
    }
    options.update(properties or {})
    return [str(java)] + [f"-D{key}={value}" for key, value in options.items()]


def _clean(stream: str) -> str:
    return "\n".join(line for line in stream.splitlines() if not line.startswith("Picked up "))


def run_jython(
    script: str | Path,
    *args: str,
    headless: bool = True,
    cwd: Path | None = None,
    timeout: int = 120,
    properties: dict[str, str] | None = None,
) -> str:
    """Run `java -jar jython-standalone.jar script args` and return stdout; a non-zero exit raises."""
    java, jar = require()
    path = Path(script)
    if not path.is_absolute():
        path = SCRIPTS / path
    command = _base_command(java, headless, properties) + ["-jar", str(jar), str(path), *args]
    done = subprocess.run(command, capture_output=True, text=True, cwd=cwd, timeout=timeout, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"{path.name} exited with {done.returncode}:\n{_clean(done.stderr or done.stdout)[-600:]}")
    return _clean(done.stdout)


def launch_jython(script: str | Path, *args: str) -> subprocess.Popen:
    """Start a Jython GUI script and leave it running (used by the window buttons)."""
    java, jar = require()
    path = Path(script)
    if not path.is_absolute():
        path = SCRIPTS / path
    command = _base_command(java, False, None) + ["-jar", str(jar), str(path), *args]
    return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def build_jar() -> Path:
    """Compile lab4/java/com/MyClass.java into a jar that Jython can put on sys.path."""
    javac, jar_tool = find_tool("javac"), find_tool("jar")
    if javac is None or jar_tool is None:
        raise JythonUnavailable("javac/jar not found: a JDK (not only a JRE) is needed")
    classes = WORK_DIR / "classes"
    shutil.rmtree(classes, ignore_errors=True)
    classes.mkdir(parents=True)
    subprocess.run([str(javac), "-d", str(classes), str(JAVA_SOURCES / "com" / "MyClass.java")], check=True, capture_output=True)
    target = WORK_DIR / "myclass.jar"
    subprocess.run([str(jar_tool), "cf", str(target), "-C", str(classes), "com"], check=True, capture_output=True)
    return target


def run_java_embedding() -> str:
    """Compile and run JythonHelloWorld: Java is the host, Jython is a library inside it."""
    java, jar = require()
    javac = find_tool("javac")
    if javac is None:
        raise JythonUnavailable("javac not found: a JDK (not only a JRE) is needed")
    classes = WORK_DIR / "embed"
    shutil.rmtree(classes, ignore_errors=True)
    classes.mkdir(parents=True)
    subprocess.run(
        [str(javac), "-cp", str(jar), "-d", str(classes), str(JAVA_SOURCES / "JythonHelloWorld.java")],
        check=True,
        capture_output=True,
    )
    command = _base_command(java, True, {"python.path": str(SCRIPTS)}) + [
        "-cp",
        os.pathsep.join([str(classes), str(jar)]),
        "JythonHelloWorld",
    ]
    done = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    if done.returncode != 0:
        raise RuntimeError(_clean(done.stderr)[-600:])
    return _clean(done.stdout)


def display_available() -> bool:
    """True when AWT can open a window (macOS and Windows always have one; Linux needs $DISPLAY)."""
    if os.name == "nt" or os.uname().sysname == "Darwin":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
