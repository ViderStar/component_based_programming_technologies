"""Image helpers: WebP/PNG bytes <-> wx.Bitmap via Pillow."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

from configs.cfg import ICONS_DIR


def read_image_bytes(path: str | Path) -> bytes:
    return Path(path).read_bytes()


def sniff_mime(path: str | Path, data: bytes | None = None) -> str:
    suffix = Path(path).suffix.lower()
    mapping = {
        ".webp": "image/webp",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    if suffix in mapping:
        return mapping[suffix]
    if data and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def bytes_to_pil(data: bytes) -> Image.Image:
    image = Image.open(BytesIO(data))
    image.load()
    return image.convert("RGBA")


def pil_to_wx_bitmap(image: Image.Image, max_size: tuple[int, int] | None = None):
    import wx

    work = image.convert("RGB")
    if max_size is not None:
        work = work.copy()
        work.thumbnail(max_size, Image.Resampling.LANCZOS)
    wx_image = wx.Image(*work.size)
    wx_image.SetData(work.tobytes())
    return wx_image.ConvertToBitmap()


def bytes_to_wx_bitmap(data: bytes, max_size: tuple[int, int] | None = (320, 240)):
    return pil_to_wx_bitmap(bytes_to_pil(data), max_size=max_size)


def load_icon(name: str, size: tuple[int, int] = (32, 32)):
    import wx

    path = ICONS_DIR / f"{name}.png"
    if not path.exists():
        bitmap = wx.Bitmap(*size)
        return bitmap
    image = Image.open(path).convert("RGBA")
    image = image.resize(size, Image.Resampling.LANCZOS)
    rgb = image.convert("RGB")
    wx_image = wx.Image(*rgb.size)
    wx_image.SetData(rgb.tobytes())
    alpha = image.getchannel("A").tobytes()
    wx_image.SetAlphaBuffer(alpha)
    return wx_image.ConvertToBitmap()
