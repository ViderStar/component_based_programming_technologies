"""Open documents and desktop applications in a cross-platform way."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def open_path(path: str | Path) -> None:
    target = str(path)
    if sys.platform == "darwin":
        subprocess.Popen(["open", target])
        return
    if sys.platform == "win32":
        os.startfile(target)  # type: ignore[attr-defined]
        return
    subprocess.Popen(["xdg-open", target])


def _mac_open_app(app_names: list[str], document: Path | None = None) -> str:
    for name in app_names:
        check = subprocess.run(
            ["mdfind", f"kMDItemCFBundleName == '{name}'"],
            capture_output=True,
            text=True,
            check=False,
        )
        if not check.stdout.strip() and not Path(f"/Applications/{name}.app").exists():
            continue
        cmd = ["open", "-a", name]
        if document is not None:
            cmd.append(str(document))
        subprocess.Popen(cmd)
        return name
    if document is not None:
        open_path(document)
        return "системное приложение"
    raise FileNotFoundError(f"Не найдены приложения: {', '.join(app_names)}")


def open_word(document: Path | None = None) -> str:
    if sys.platform == "darwin":
        return _mac_open_app(["Microsoft Word", "Pages", "TextEdit"], document)
    if sys.platform == "win32":
        if document:
            os.startfile(document)  # type: ignore[attr-defined]
            return "ассоциированное приложение Windows"
        subprocess.Popen(["cmd", "/c", "start", "winword"])
        return "Microsoft Word"
    binary = shutil.which("libreoffice") or shutil.which("soffice")
    if binary:
        cmd = [binary]
        if document:
            cmd.append(str(document))
        subprocess.Popen(cmd)
        return "LibreOffice"
    if document:
        open_path(document)
        return "xdg-open"
    raise FileNotFoundError("Текстовый процессор не найден")


def open_excel(document: Path | None = None) -> str:
    if sys.platform == "darwin":
        return _mac_open_app(["Microsoft Excel", "Numbers", "TextEdit"], document)
    if sys.platform == "win32":
        if document:
            os.startfile(document)  # type: ignore[attr-defined]
            return "ассоциированное приложение Windows"
        subprocess.Popen(["cmd", "/c", "start", "excel"])
        return "Microsoft Excel"
    binary = shutil.which("libreoffice") or shutil.which("soffice")
    if binary:
        cmd = [binary]
        if document:
            cmd.append(str(document))
        subprocess.Popen(cmd)
        return "LibreOffice"
    if document:
        open_path(document)
        return "xdg-open"
    raise FileNotFoundError("Табличный процессор не найден")


def open_calendar() -> str:
    if sys.platform == "darwin":
        subprocess.Popen(["open", "-a", "Calendar"])
        return "Calendar"
    if sys.platform == "win32":
        subprocess.Popen(["cmd", "/c", "start", "outlookcal:"], shell=False)
        return "Календарь Windows"
    subprocess.Popen(["gnome-calendar"])
    return "gnome-calendar"


def play_audio(path: str | Path) -> str:
    target = str(path)
    try:
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(target)
        pygame.mixer.music.play()
        return "pygame"
    except Exception:
        if sys.platform == "darwin":
            subprocess.Popen(["afplay", target])
            return "afplay"
        if sys.platform == "win32":
            os.startfile(target)  # type: ignore[attr-defined]
            return "Windows Media"
        subprocess.Popen(["xdg-open", target])
        return "xdg-open"


def stop_audio() -> None:
    try:
        import pygame

        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass
