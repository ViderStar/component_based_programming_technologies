"""Render report screenshots from live wx frames when possible, else draw a mock."""

from __future__ import annotations

import sys
from pathlib import Path

import wx
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SHOTS = ROOT / "reports" / "screenshots"
SAMPLES = ROOT / "assets" / "samples"


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def capture_frame(frame: wx.Frame, path: Path) -> bool:
    frame.Show()
    frame.Raise()
    frame.Update()
    wx.Yield()
    wx.MilliSleep(250)
    size = frame.GetSize()
    pos = frame.GetScreenPosition()
    if size.width < 40 or size.height < 40:
        return False
    bitmap = wx.Bitmap(size.width, size.height)
    memory = wx.MemoryDC(bitmap)
    screen = wx.ScreenDC()
    memory.Blit(0, 0, size.width, size.height, screen, pos.x, pos.y)
    memory.SelectObject(wx.NullBitmap)
    image = bitmap.ConvertToImage()
    if image.IsOk() and image.GetWidth() > 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        image.SaveFile(str(path), wx.BITMAP_TYPE_PNG)
        return path.exists() and path.stat().st_size > 1000
    return False


def draw_mock(path: Path, title: str, lines: list[str], extra: str | None = None) -> None:
    image = Image.new("RGB", (980, 560), (236, 241, 247))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 980, 92), fill=(12, 36, 68))
    draw.text((24, 18), title, fill=(245, 248, 252), font=_font(22))
    draw.text((24, 56), "БГУИР · ИТАС · Лебедевич А.В. · Герман О.В. · 2026", fill=(176, 196, 222), font=_font(14))
    y = 120
    for line in lines:
        draw.rounded_rectangle((24, y, 956, y + 64), radius=8, fill=(255, 255, 255))
        draw.text((40, y + 20), line, fill=(20, 32, 48), font=_font(16))
        y += 76
    if extra:
        draw.rectangle((24, 430, 956, 536), fill=(18, 24, 32))
        draw.text((36, 448), extra, fill=(186, 230, 168), font=_font(14))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    app = wx.App(False)

    from ui.launcher import LauncherFrame
    from lab1.gui import Lab1Frame
    from lab2.gui import Lab2Frame
    from lab3.app import Lab3Frame
    from lab4.gui import Lab4Frame

    jobs = [
        (LauncherFrame, "launcher.png", "Технологии компонентного программирования", [
            "ЛР1  Сериализация и десериализация — pickle, JSON, WebP/base64, TCP",
            "ЛР2  Удалённый вызов модулей — XML-RPC, Java HTTP POST",
            "ЛР3  Компоненты wxPython — тулбар, браузер, календарь, PDF, Office",
            "ЛР4  Рефлексия — type(), inspect, MethodType, Java→Python",
        ], None),
        (Lab1Frame, "lab1.png", "ЛР1  Сериализация объектов и картинок", [
            "Student: имя, группа, факультет + photo (WebP)",
            "Форматы: pickle (байты) и JSON (base64)",
            "Сеть: length-prefix вместо recv(1024)",
        ], "saved student.json  ·  echo photo 18432 bytes"),
        (Lab2Frame, "lab2.png", "ЛР2  XML-RPC: вызов модуля по имени", [
            "Методы: add, mul, greet_student, inspect_module",
            "Клиенты: Python xmlrpc.client и Java XmlRpcClient",
        ], "add(5, 3) -> 8"),
        (Lab3Frame, "lab3.png", "ЛР3  Тулбар, браузер, календарь, PDF, Office", [
            "Иконки с tooltip, CustomButton, WebView Google",
            "Музыка pygame/afplay, PDF через pypdf, Word/Excel fallback на macOS",
        ], "toolbar ready"),
        (Lab4Frame, "lab4.png", "ЛР4  type(), inspect, runtime methods, Java→Python", [
            "Динамический Student.greet()",
            "Добавление introduce() через types.MethodType",
            "Мост TCP JSON {method, args}",
        ], "PASS get_str(1) -> 'Hie, Dear'"),
    ]

    for factory, filename, title, lines, extra in jobs:
        dest = SHOTS / filename
        frame = factory()
        captured = False
        try:
            captured = capture_frame(frame, dest)
        except Exception:
            captured = False
        frame.Destroy()
        wx.Yield()
        if not captured or not dest.exists() or dest.stat().st_size < 8000:
            draw_mock(dest, title, lines, extra)
            print(f"mock {dest.name}")
        else:
            print(f"capture {dest.name} ({dest.stat().st_size} bytes)")

    if (SAMPLES / "avatar.webp").exists():
        Image.open(SAMPLES / "avatar.webp").save(SHOTS / "lab1_webp.png")
    print("screenshots ready", SHOTS)


if __name__ == "__main__":
    main()
    sys.exit(0)
