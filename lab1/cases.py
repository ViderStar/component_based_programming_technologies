"""Checkable scenarios for lab 1 (files, base64, sockets, GUI snapshot)."""

from __future__ import annotations

from configs.cfg import ARTIFACTS_DIR, SAMPLES_DIR
from helpers.paths import ensure_artifacts_dir
from lab1.client import send_student
from lab1.codecs import attach_photo, dumps_json, dumps_pickle, loads_json_form, loads_json_student, loads_pickle
from lab1.models import GuiFormState, Student
from lab1.reader import load_student
from lab1.server import StudentServer

_SERVER: StudentServer | None = None


def sample_student(base: Student) -> Student:
    photo = SAMPLES_DIR / "avatar.webp"
    if photo.exists() and base.photo is None:
        attach_photo(base, photo)
    return base


def ensure_server() -> StudentServer:
    global _SERVER
    if _SERVER is None or not _SERVER.running:
        _SERVER = StudentServer()
        _SERVER.start()
    return _SERVER


def stop_server() -> None:
    global _SERVER
    if _SERVER is not None:
        _SERVER.stop()
        _SERVER = None


def pickle_file(student: Student) -> str:
    ensure_artifacts_dir()
    path = ARTIFACTS_DIR / "student.pkl"
    path.write_bytes(dumps_pickle(student))
    restored = loads_pickle(path.read_bytes())
    if not isinstance(restored, Student) or restored.name != student.name:
        raise AssertionError("pickle mismatch")
    if student.photo and (restored.photo is None or restored.photo.data != student.photo.data):
        raise AssertionError("webp bytes lost in pickle")
    size = len(student.photo.data) if student.photo else 0
    return f"{path.name}, photo {size} B"


def json_base64(student: Student) -> str:
    ensure_artifacts_dir()
    path = ARTIFACTS_DIR / "student.json"
    path.write_bytes(dumps_json(student))
    restored = loads_json_student(path.read_bytes())
    if restored.name != student.name:
        raise AssertionError("json mismatch")
    if student.photo:
        if restored.photo is None or restored.photo.data != student.photo.data:
            raise AssertionError("base64 webp mismatch")
        if restored.photo.mime != "image/webp":
            raise AssertionError(restored.photo.mime)
        text = path.read_text(encoding="utf-8")
        if "base64" not in text:
            raise AssertionError("no base64 field")
    return f"{path.name}, base64 webp"


def other_app_reader(student: Student) -> str:
    pickle_file(student)
    json_base64(student)
    a = load_student(ARTIFACTS_DIR / "student.pkl")
    b = load_student(ARTIFACTS_DIR / "student.json")
    if a.name != b.name:
        raise AssertionError("reader pickle/json diverge")
    return "lab1.reader pkl+json"


def tcp_roundtrip(student: Student, fmt: str) -> str:
    ensure_server()
    echoed = send_student(student, fmt=fmt)
    if echoed.name != student.name:
        raise AssertionError("echo name")
    if student.photo:
        if echoed.photo is None or len(echoed.photo.data) != len(student.photo.data):
            raise AssertionError("photo truncated on socket")
        return f"{fmt} {len(echoed.photo.data)} B photo"
    return fmt


def gui_form(student: Student) -> GuiFormState:
    ensure_artifacts_dir()
    state = GuiFormState(title="Form", button_label="OK", text_value=student.name, label_text="GUI")
    path = ARTIFACTS_DIR / "gui_form.json"
    path.write_bytes(dumps_json(state))
    restored = loads_json_form(path.read_bytes())
    if restored.text_value != student.name:
        raise AssertionError("form snapshot")
    return restored
