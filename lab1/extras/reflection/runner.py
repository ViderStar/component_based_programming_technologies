"""CLI demo for dynamic classes, inspect, runtime methods, Java bridge."""

from __future__ import annotations

import logging

from lab1.extras.reflection.bridge_server import MethodBridge, send_request
from lab1.extras.reflection.dynamic_student import Student, make_student
from lab1.extras.reflection.inspector import format_report
from lab1.extras.reflection.runtime_methods import add_method_to_class, add_method_to_object, introduce, run_annotated_tests

logger = logging.getLogger(__name__)


def run_reflection() -> dict[str, object]:
    student = make_student()
    logger.info("Dynamic class: %s", Student)
    logger.info(format_report(student))

    add_method_to_object(student, "introduce", introduce)
    logger.info("Instance method: %s", student.introduce("BSUIR"))

    add_method_to_class(Student, "shout", lambda self: self.greet().upper())
    logger.info("Class method: %s", student.shout())

    tests = run_annotated_tests()
    for line in tests:
        logger.info("annotation test: %s", line)

    bridge = MethodBridge()
    bridge.start()
    try:
        greet = send_request("greet")
        intro = send_request("introduce", ["Java"])
        logger.info("bridge greet: %s", greet)
        logger.info("bridge introduce: %s", intro)
    finally:
        bridge.stop()

    return {"greet": student.greet(), "tests": tests}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_reflection()
