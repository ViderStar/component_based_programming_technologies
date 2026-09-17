"""Shared wxPython look: BSUIR blue header, cards, log boxes."""

from __future__ import annotations

import wx

from configs.cfg import COURSE, STUDENT_NAME, STUDENT_ROLE, TEACHER_NAME, YEAR
from helpers.images import load_icon

BSUIR_BLUE = wx.Colour(0, 85, 165)
HEADER_BG = wx.Colour(12, 36, 68)
HEADER_FG = wx.Colour(245, 248, 252)
ACCENT = wx.Colour(30, 144, 210)
CARD_BG = wx.Colour(255, 255, 255)
PAGE_BG = wx.Colour(236, 241, 247)
MUTED = wx.Colour(90, 104, 122)


def apply_window_icon(window: wx.TopLevelWindow) -> None:
    try:
        icon = wx.Icon()
        icon.CopyFromBitmap(load_icon("app", (64, 64)))
        window.SetIcon(icon)
    except Exception:
        pass


def styled_button(parent: wx.Window, label: str, primary: bool = True) -> wx.Button:
    button = wx.Button(parent, label=label, size=(-1, 36))
    if primary:
        button.SetBackgroundColour(BSUIR_BLUE)
        button.SetForegroundColour(wx.WHITE)
    return button


def make_header(
    parent: wx.Window,
    title: str,
    subtitle: str | None = None,
) -> wx.Panel:
    panel = wx.Panel(parent, size=(-1, 92))
    panel.SetBackgroundColour(HEADER_BG)
    sizer = wx.BoxSizer(wx.VERTICAL)
    title_label = wx.StaticText(panel, label=title)
    title_font = wx.Font(16, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    title_label.SetFont(title_font)
    title_label.SetForegroundColour(HEADER_FG)
    sizer.Add(title_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 14)

    if subtitle is None:
        subtitle = f"{COURSE}  ·  {STUDENT_NAME}, {STUDENT_ROLE}  ·  {TEACHER_NAME}  ·  {YEAR}"
    sub_label = wx.StaticText(panel, label=subtitle)
    sub_label.SetForegroundColour(wx.Colour(176, 196, 222))
    sizer.Add(sub_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)
    panel.SetSizer(sizer)
    return panel


def make_card(parent: wx.Window) -> wx.Panel:
    card = wx.Panel(parent)
    card.SetBackgroundColour(CARD_BG)
    return card


def make_log(parent: wx.Window, height: int = 180) -> wx.TextCtrl:
    log = wx.TextCtrl(
        parent,
        style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP | wx.BORDER_SIMPLE,
        size=(-1, height),
    )
    log.SetBackgroundColour(wx.Colour(18, 24, 32))
    log.SetForegroundColour(wx.Colour(186, 230, 168))
    log.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    return log


def append_log(log: wx.TextCtrl, message: str) -> None:
    log.AppendText(message.rstrip() + "\n")
    log.ShowPosition(log.GetLastPosition())
