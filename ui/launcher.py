"""Launcher: two labs plus the Lab 1 extras, no walls of text."""

from __future__ import annotations

import wx

from configs.cfg import COURSE, STUDENT_NAME, TEACHER_NAME, YEAR
from ui.theme import MUTED, PAGE_BG, apply_window_icon, make_header, styled_button

LABS = [
    ("Lab 1  Serialization", "lab1"),
    ("Lab 2  COM server", "lab2"),
]
EXTRAS = [
    ("XML-RPC", "rpc"),
    ("wxPython", "wxui"),
    ("Reflection", "reflection"),
]


class LauncherFrame(wx.Frame):
    def __init__(self) -> None:
        super().__init__(None, title=COURSE, size=(640, 360))
        apply_window_icon(self)
        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, COURSE), 0, wx.EXPAND)

        grid = wx.GridSizer(rows=1, cols=2, vgap=10, hgap=10)
        for title, lab_id in LABS:
            btn = styled_button(root, title)
            btn.Bind(wx.EVT_BUTTON, lambda _e, lab=lab_id: self.open_lab(lab))
            grid.Add(btn, 0, wx.EXPAND)
        layout.Add(grid, 1, wx.ALL | wx.EXPAND, 16)

        caption = wx.StaticText(root, label="Lab 1 extras")
        caption.SetForegroundColour(MUTED)
        layout.Add(caption, 0, wx.LEFT | wx.RIGHT, 16)
        extras = wx.GridSizer(rows=1, cols=3, vgap=10, hgap=10)
        for title, lab_id in EXTRAS:
            btn = styled_button(root, title, primary=False)
            btn.Bind(wx.EVT_BUTTON, lambda _e, lab=lab_id: self.open_lab(lab))
            extras.Add(btn, 0, wx.EXPAND)
        layout.Add(extras, 0, wx.ALL | wx.EXPAND, 16)
        root.SetSizer(layout)

        menubar = wx.MenuBar()
        help_menu = wx.Menu()
        about = help_menu.Append(wx.ID_ABOUT, "About")
        self.Bind(wx.EVT_MENU, self._on_about, about)
        menubar.Append(help_menu, "Help")
        self.SetMenuBar(menubar)
        self.Centre()

    def _on_about(self, _event: wx.Event) -> None:
        wx.MessageBox(
            f"{STUDENT_NAME}\n{TEACHER_NAME}\n{YEAR}",
            "About",
            wx.OK | wx.ICON_INFORMATION,
            self,
        )

    def open_lab(self, lab_id: str) -> None:
        if lab_id == "lab1":
            from lab1.gui import Lab1Frame

            Lab1Frame(self).Show()
        elif lab_id == "lab2":
            from lab2.gui import Lab2Frame

            Lab2Frame(self).Show()
        elif lab_id == "rpc":
            from lab1.extras.rpc.gui import RpcFrame

            RpcFrame(self).Show()
        elif lab_id == "wxui":
            from lab1.extras.wxui.app import WxuiFrame

            WxuiFrame(self).Show()
        else:
            from lab1.extras.reflection.gui import ReflectionFrame

            ReflectionFrame(self).Show()


def run_launcher() -> None:
    app = wx.GetApp() or wx.App(False)
    LauncherFrame().Show()
    app.MainLoop()
