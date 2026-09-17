"""Compact XML-RPC lab: cases cover the protocol."""

from __future__ import annotations

import wx

from lab2 import cases
from ui.cases import CasePanel
from ui.theme import PAGE_BG, apply_window_icon, make_header


class Lab2Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="Lab 2", size=(720, 420))
        apply_window_icon(self)
        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "Lab 2  XML-RPC"), 0, wx.EXPAND)
        layout.Add(
            CasePanel(
                root,
                [
                    ("add(2, 3)", cases.add),
                    ("mul(6, 7)", cases.mul),
                    ("greet_student", cases.greet),
                    ("inspect + listMethods", cases.inspect),
                    ("Java client", cases.java_client),
                ],
            ),
            1,
            wx.EXPAND | wx.ALL,
            10,
        )
        root.SetSizer(layout)
        self.Bind(wx.EVT_CLOSE, self._on_close)

    def _on_close(self, event: wx.CloseEvent) -> None:
        cases.stop_server()
        event.Skip()
