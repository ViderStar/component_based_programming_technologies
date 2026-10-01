"""CLI demo for the COM calculator: register, activate, call, fail, unregister."""

from __future__ import annotations

import logging

from lab2 import cases, registry

logger = logging.getLogger(__name__)


def run_lab2() -> dict[str, str]:
    try:
        results = {"register": cases.register()}
        for key, value in registry.entries().items():
            logger.info("%s = %s", key, value)
        results["dispatch"] = cases.dispatch()
        results["arithmetic"] = cases.arithmetic(trace=logger.info)
        results["com_errors"] = cases.com_errors()
        results["excel_sheet"] = cases.excel_sheet()
        results["html_client"] = cases.html_client()
        results["unregister"] = cases.unregister()
        for key, value in results.items():
            logger.info("%s -> %s", key, value)
        return results
    finally:
        cases.stop_web()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_lab2()
