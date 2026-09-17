"""CLI demo for dynamic classes, inspect, runtime methods, Java bridge."""

from __future__ import annotations

import logging

from lab4.bridge_server import MethodBridge, send_request
from lab4.dynamic_student import Student, make_student
from lab4.inspector import format_report
from lab4.runtime_methods import add_method_to_class, add_method_to_object, introduce, run_annotated_tests

logger = logging.getLogger(__name__)


def run_lab4() -> dict[str, object]:
    student = make_student()
    logger.info("Динамический класс: %s", Student)
    logger.info(format_report(student))

    add_method_to_object(student, "introduce", introduce)
    logger.info("Метод на объекте: %s", student.introduce("БГУИР"))

    add_method_to_class(Student, "shout", lambda self: self.greet().upper())
    logger.info("Метод на классе: %s", student.shout())

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
    run_lab4()
