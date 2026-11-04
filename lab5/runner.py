"""CLI demo for the JSP lab: build the war, start Tomcat and check every page."""

from __future__ import annotations

import logging

from lab5 import cases, runtime

logger = logging.getLogger(__name__)

CASES = (
    ("environment", cases.environment),
    ("war_build", cases.war_build),
    ("today_page", cases.today_page),
    ("hello_prototype", cases.hello_prototype),
    ("currency_rates", cases.currency_rates),
    ("image_png", cases.image_png),
    ("translator", cases.translator),
    ("site_writer", cases.site_writer),
)


def run_lab5() -> dict[str, str]:
    try:
        runtime.require()
    except runtime.TomcatUnavailable as exc:
        logger.info("Lab 5 skipped: %s", exc)
        return {"skipped": str(exc)}
    results: dict[str, str] = {}
    try:
        for name, case in CASES:
            results[name] = case()
            logger.info("%s -> %s", name, results[name])
    finally:
        cases.stop_server()
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_lab5()
