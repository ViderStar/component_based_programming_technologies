"""Custom wxPython widgets used by lab 3."""

from __future__ import annotations

import wx

from ui.theme import BSUIR_BLUE


class CustomButton(wx.Button):
    """Subclassed wx.Button with BSUIR colours, as in the handout."""

    def __init__(self, parent: wx.Window, label: str, tooltip: str | None = None) -> None:
        super().__init__(parent, label=label, size=(-1, 36))
        self.SetBackgroundColour(BSUIR_BLUE)
        self.SetForegroundColour(wx.WHITE)
        if tooltip:
            self.SetToolTip(tooltip)
        self.Bind(wx.EVT_BUTTON, self.on_button_click)

    def on_button_click(self, event: wx.CommandEvent) -> None:
        event.Skip()
