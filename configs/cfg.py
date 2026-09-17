"""Course metadata and network defaults."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

UNIVERSITY = (
    "Белорусский государственный университет информатики и радиоэлектроники"
)
FACULTY = "Факультет информационных технологий и управления"
DEPARTMENT = "Кафедра информационных технологий автоматизированных систем"
COURSE = "Технологии компонентного программирования"
YEAR = 2026
CITY = "Минск"

STUDENT_NAME = "Лебедевич Артём Владимирович"
STUDENT_ROLE = "магистрант 2 курса"

TEACHER_NAME = "Герман Олег Витольдович"
TEACHER_TITLE = "кандидат технических наук, доцент кафедры ИТАС"

DEFAULT_STUDENT = {
    "name": STUDENT_NAME,
    "group": "магистрант, 2 курс",
    "faculty": "ФИТУ / ИТАС",
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
