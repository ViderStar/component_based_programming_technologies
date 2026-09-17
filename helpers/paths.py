"""Filesystem helpers."""

from __future__ import annotations

from pathlib import Path

from configs.cfg import ARTIFACTS_DIR, PROJECT_ROOT


def project_root() -> Path:
    return PROJECT_ROOT


def ensure_artifacts_dir() -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR
