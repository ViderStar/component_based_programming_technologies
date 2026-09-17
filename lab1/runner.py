"""CLI walkthrough of lab 1: files, pickle/JSON, sockets, GUI snapshot."""

from __future__ import annotations

import logging
from pathlib import Path

from configs.cfg import ARTIFACTS_DIR, DEFAULT_STUDENT, LAB1_PORT, SAMPLES_DIR
from helpers.paths import ensure_artifacts_dir
from lab1.client import send_student
from lab1.codecs import attach_photo, dumps_json, dumps_pickle, loads_json_form, loads_json_student, loads_pickle
from lab1.models import GuiFormState, Student
from lab1.reader import load_student
from lab1.server import StudentServer

logger = logging.getLogger(__name__)


def _sample_photo() -> Path | None:
    candidate = SAMPLES_DIR / "avatar.webp"
    return candidate if candidate.exists() else None


def build_demo_student() -> Student:
    student = Student(**DEFAULT_STUDENT)
    photo = _sample_photo()
    if photo is not None:
        attach_photo(student, photo)
    return student


def run_lab1() -> Student:
    ensure_artifacts_dir()
    student = build_demo_student()
    logger.info("Student: %s", student.greet())
    if student.photo:
        logger.info(
            "Photo: %s, %s, %s bytes",
            student.photo.filename,
            student.photo.mime,
            len(student.photo.data),
        )

    pkl_path = ARTIFACTS_DIR / "student.pkl"
    json_path = ARTIFACTS_DIR / "student.json"
    pkl_path.write_bytes(dumps_pickle(student))
    json_path.write_bytes(dumps_json(student))
    logger.info("pickle file: %s (%s bytes)", pkl_path.name, pkl_path.stat().st_size)
    logger.info("JSON file:   %s (%s bytes)", json_path.name, json_path.stat().st_size)

    via_pickle = load_student(pkl_path)
    via_json = loads_json_student(json_path.read_bytes())
    logger.info("Other process (reader) pickle: %s", via_pickle.greet())
    logger.info("JSON roundtrip: %s, photo=%s", via_json.greet(), via_json.photo)

    form = GuiFormState(text_value=student.name, label_text="demo")
    form_path = ARTIFACTS_DIR / "gui_form.json"
    form_path.write_bytes(dumps_json(form))
    restored = loads_json_form(form_path.read_bytes())
    logger.info("GUI snapshot: %s", restored.to_dict())

    server = StudentServer()
    received: list[Student] = []
    server.on_student = lambda item, fmt: received.append(item)
    try:
        server.start()
        echoed = send_student(student, fmt="json")
        logger.info("Network JSON echo: %s", echoed.greet())
        echoed_p = send_student(student, fmt="pickle")
        logger.info("Network pickle echo: %s", echoed_p.greet())
        if echoed.photo:
            logger.info("Photo sent over the wire: %s bytes (port %s)", len(echoed.photo.data), LAB1_PORT)
    finally:
        server.stop()

    _ = loads_pickle(pkl_path.read_bytes())
    logger.info("Lab 1 done")
    return student


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_lab1()
