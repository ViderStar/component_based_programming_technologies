"""CLI smoke-test for lab 3 helpers (no window)."""

from __future__ import annotations

import logging
from pathlib import Path

from configs.cfg import ICONS_DIR, SAMPLES_DIR
from lab3.actions import extract_pdf_text
from lab3.widgets import CustomButton

logger = logging.getLogger(__name__)


def run_lab3() -> dict[str, object]:
    pdf = SAMPLES_DIR / "sample.pdf"
    text = extract_pdf_text(pdf) if pdf.exists() else ""
    icons = sorted(path.name for path in ICONS_DIR.glob("*.png"))
    logger.info("CustomButton bases: %s", CustomButton.__mro__)
    logger.info("Иконки тулбара: %s", ", ".join(icons) or "(ещё не сгенерированы)")
    if text:
        logger.info("PDF preview:\n%s", text[:400])
    return {"icons": icons, "pdf_chars": len(text)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_lab3()
