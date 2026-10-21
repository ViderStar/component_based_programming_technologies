"""CLI demo for the Brython lab: the three numerical tasks and the page that runs them in a browser."""

from __future__ import annotations

import logging

from lab3 import cases, numerics

logger = logging.getLogger(__name__)


def run_lab3() -> dict[str, str]:
    try:
        results = {"site_files": cases.site_files()}
        for coeffs in numerics.DEMO_POLYNOMIALS[:3]:
            roots = ", ".join(numerics.root_text(r) for r in numerics.poly_roots(coeffs))
            logger.info("%s -> %s", numerics.poly_text(coeffs), roots)
        results["polynomial_roots"] = cases.polynomial_roots()
        results["regression"] = cases.regression()
        results["optimum"] = cases.optimum()
        results["handout_examples"] = cases.handout_examples()
        results["brython_page"] = cases.brython_page()
        for key, value in results.items():
            logger.info("%s -> %s", key, value)
        return results
    finally:
        cases.stop_server()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_lab3()
