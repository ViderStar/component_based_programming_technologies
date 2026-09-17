"""Lab 3 side effects: files, office apps, PDF text extraction."""

from __future__ import annotations

from pathlib import Path

from helpers.office import open_excel, open_path, open_word, play_audio, stop_audio
from pypdf import PdfReader


def extract_pdf_text(path: str | Path, max_pages: int = 8) -> str:
    reader = PdfReader(str(path))
    chunks: list[str] = []
    for index, page in enumerate(reader.pages[:max_pages], start=1):
        text = page.extract_text() or ""
        chunks.append(f"— страница {index} —\n{text.strip()}")
    return "\n\n".join(chunks) if chunks else "(текст не извлечён)"


__all__ = ["extract_pdf_text", "open_excel", "open_path", "open_word", "play_audio", "stop_audio"]
