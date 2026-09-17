#!/usr/bin/env python3
"""Generate sample WebP, PDF, WAV, RTF, CSV and toolbar icons."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "assets" / "icons"
SAMPLES = ROOT / "assets" / "samples"

PALETTE = {
    "app": (12, 36, 68),
    "image": (0, 85, 165),
    "music": (156, 39, 176),
    "browser": (0, 150, 136),
    "word": (43, 87, 154),
    "excel": (33, 115, 70),
    "calendar": (230, 126, 34),
    "pdf": (192, 57, 43),
}


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def make_icon(name: str, color: tuple[int, int, int], glyph: str) -> None:
    image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 120, 120), radius=28, fill=color)
    font = _font(48)
    bbox = draw.textbbox((0, 0), glyph, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((128 - tw) / 2 - bbox[0], (128 - th) / 2 - bbox[1]), glyph, fill="white", font=font)
    image.save(ICONS / f"{name}.png")


def make_avatar() -> None:
    image = Image.new("RGB", (480, 480), (12, 36, 68))
    draw = ImageDraw.Draw(image)
    draw.ellipse((90, 70, 390, 370), fill=(0, 85, 165))
    draw.ellipse((175, 140, 305, 270), fill=(236, 241, 247))
    draw.pieslice((120, 280, 360, 520), 200, 340, fill=(236, 241, 247))
    draw.text((40, 420), "BSUIR · 2026", fill=(176, 196, 222), font=_font(28))
    image.save(SAMPLES / "avatar.webp", "WEBP", quality=80)
    image.save(SAMPLES / "avatar.png", "PNG")


def make_wav() -> None:
    path = SAMPLES / "sample.wav"
    rate = 22050
    seconds = 1.2
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        frames = bytearray()
        for index in range(int(rate * seconds)):
            t = index / rate
            sample = int(12000 * math.sin(2 * math.pi * 440 * t) * (1 - t / seconds))
            frames.extend(struct.pack("<h", sample))
        wav.writeframes(frames)


def make_pdf() -> None:
    content = "BT /F1 16 Tf 40 700 Td (Component-based programming) Tj 0 -28 Td (BSUIR ITAS 2026) Tj 0 -28 Td (Lebedevich A.V.) Tj ET"
    stream = content.encode("ascii")
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 780] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n{body}\nendobj\n".encode("ascii"))
    xref_at = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode("ascii")
    )
    (SAMPLES / "sample.pdf").write_bytes(out)


def make_office() -> None:
    (SAMPLES / "sample.rtf").write_text(
        r"{\rtf1\ansi\deff0{\fonttbl{\f0 Helvetica;}}\f0\fs28 "
        r"BSUIR 2026. Lab 3 sample document for Word/Pages/TextEdit.\par}",
        encoding="ascii",
    )
    (SAMPLES / "sample.csv").write_text(
        "name,group,faculty\nLebedevich,master-2,FITU-ITAS\n",
        encoding="utf-8",
    )


def main() -> None:
    ICONS.mkdir(parents=True, exist_ok=True)
    SAMPLES.mkdir(parents=True, exist_ok=True)
    glyphs = {
        "app": "TK",
        "image": "IMG",
        "music": "♪",
        "browser": "WWW",
        "word": "W",
        "excel": "X",
        "calendar": "31",
        "pdf": "PDF",
    }
    for name, color in PALETTE.items():
        make_icon(name, color, glyphs[name])
    make_avatar()
    make_wav()
    make_pdf()
    make_office()
    print("assets ready")


if __name__ == "__main__":
    main()
