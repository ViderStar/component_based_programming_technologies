"""Checkable reflection scenarios."""

from __future__ import annotations

import inspect
import subprocess

from configs.cfg import LAB4_HOST, LAB4_PORT, PROJECT_ROOT
from lab4.bridge_server import MethodBridge, send_request
from lab4.dynamic_student import Student, make_student
from lab4.inspector import describe
from lab4.runtime_methods import add_method_to_object, introduce, run_annotated_tests

_BRIDGE: MethodBridge | None = None
JAVA_SRC = PROJECT_ROOT / "lab4" / "java" / "MethodSender.java"


def dynamic_greet(student: Student | None = None) -> str:
    person = student or make_student()
    if type(person) is not Student:
        raise AssertionError(type(person))
    text = person.greet()
    if not text.startswith("Hello, from"):
        raise AssertionError(text)
    return text


def signatures(student: Student | None = None) -> str:
    person = student or make_student()
    members = {item.name: item for item in describe(person)}
    if "greet" not in members:
        raise AssertionError(members)
    sig = str(inspect.signature(person.greet))
    if "()" not in sig and sig != "()":
        raise AssertionError(sig)
    return f"greet{members['greet'].signature}"


def runtime_method(student: Student) -> str:
    add_method_to_object(student, "introduce", introduce)
    text = student.introduce("POIT")
    if "POIT" not in text:
        raise AssertionError(text)
    return text


def annotated() -> str:
    lines = run_annotated_tests()
    if not lines or any(not line.startswith("PASS") for line in lines):
        raise AssertionError(lines)
    return f"{len(lines)} PASS"


def ensure_bridge(student: Student) -> MethodBridge:
    global _BRIDGE
    if _BRIDGE is None or not _BRIDGE.running:
        _BRIDGE = MethodBridge()
        _BRIDGE.target = student
        add_method_to_object(student, "introduce", introduce)
        _BRIDGE.start()
    else:
        _BRIDGE.target = student
    return _BRIDGE


def stop_bridge() -> None:
    global _BRIDGE
    if _BRIDGE is not None:
        _BRIDGE.stop()
        _BRIDGE = None


def python_bridge(student: Student) -> str:
    ensure_bridge(student)
    reply = send_request("greet")
    if not reply.get("ok"):
        raise AssertionError(reply)
    return str(reply["result"])


def java_bridge(student: Student) -> str:
    ensure_bridge(student)
    if subprocess.run(["which", "javac"], capture_output=True).returncode != 0:
        raise RuntimeError("javac not found")
    work = JAVA_SRC.parent
    compiled = subprocess.run(["javac", str(JAVA_SRC)], cwd=work, capture_output=True, text=True)
    if compiled.returncode != 0:
        raise RuntimeError(compiled.stderr.strip() or "javac failed")
    ran = subprocess.run(
        ["java", "-cp", str(work), "MethodSender", LAB4_HOST, str(LAB4_PORT), "greet"],
        capture_output=True,
        text=True,
    )
    if ran.returncode != 0:
        raise RuntimeError(ran.stderr or ran.stdout)
    if "Hello" not in ran.stdout:
        raise AssertionError(ran.stdout)
    return ran.stdout.strip()
