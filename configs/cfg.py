"""Course metadata and network defaults."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

UNIVERSITY = "Belarusian State University of Informatics and Radioelectronics"
FACULTY = "Faculty of Computer Systems and Networks"
SPECIALTY = "POIT"
GROUP = "PI"
COURSE = "Component-Based Programming Technologies"
YEAR = 2026
CITY = "Minsk"

STUDENT_NAME = "Artsem Lebiadzevich"

TEACHER_NAME = "Oleg German"
TEACHER_TITLE = "PhD, Associate Professor, ITAS"

DEFAULT_STUDENT = {
    "name": STUDENT_NAME,
    "group": GROUP,
    "faculty": "FCSN / POIT",
}

LAB1_HOST = "127.0.0.1"
LAB1_PORT = 8003
LAB2_HOST = "127.0.0.1"
LAB2_PORT = 8000
LAB4_HOST = "127.0.0.1"
LAB4_PORT = 8010

ASSETS_DIR = PROJECT_ROOT / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
SAMPLES_DIR = ASSETS_DIR / "samples"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DOCS_DIR = PROJECT_ROOT / "docs"
