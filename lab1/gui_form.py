"""Tiny serializable wx form (button + text field)."""

from __future__ import annotations

import wx

from lab1.models import GuiFormState


class VisualFormFrame(wx.Frame):
    def __init__(self, parent: wx.Window | None, state: GuiFormState) -> None:
        super().__init__(parent, title=state.title, size=(360, 180))
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.label = wx.StaticText(panel, label=state.label_text)
        self.text = wx.TextCtrl(panel, value=state.text_value)
        self.button = wx.Button(panel, label=state.button_label)
        self.button.Bind(wx.EVT_BUTTON, self._on_click)
        sizer.Add(self.label, 0, wx.ALL, 10)
        sizer.Add(self.text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer.Add(self.button, 0, wx.ALL, 10)
        panel.SetSizer(sizer)
        self.state = state

    def _on_click(self, _event: wx.Event) -> None:
        self.label.SetLabel(self.text.GetValue() or "OK")
        self.state.label_text = self.label.GetLabel()
        self.state.text_value = self.text.GetValue()
