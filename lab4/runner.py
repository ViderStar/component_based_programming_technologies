"""CLI demo for the Jython lab: Java from Python, Python from Java, and the menu application."""

from __future__ import annotations

import logging

from lab4 import cases, runtime

logger = logging.getLogger(__name__)

CASES = (
    ("environment", cases.environment),
    ("hello_world", cases.hello_world),
    ("files", cases.files),
    ("python_class_extends_java", cases.python_class_extends_java),
    ("java_collections", cases.java_collections),
    ("jar_import", cases.jar_import),
    ("java_calls_python", cases.java_calls_python),
    ("images_and_sound", cases.images_and_sound),
    ("menu_items", cases.menu_items),
    ("menu_picture1", cases.menu_picture1),
    ("menu_picture2", cases.menu_picture2),
    ("menu_sine", cases.menu_sine),
    ("menu_window", cases.menu_window),
    ("swing_window", cases.swing_window),
)


def run_lab4() -> dict[str, str]:
    try:
        runtime.require()
    except runtime.JythonUnavailable as exc:
        logger.info("Lab 4 skipped: %s", exc)
        return {"skipped": str(exc)}
    results: dict[str, str] = {}
    for name, case in CASES:
        results[name] = case()
        logger.info("%s -> %s", name, results[name])
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_lab4()
