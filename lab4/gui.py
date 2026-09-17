"""Compact reflection lab: tree + cases."""

from __future__ import annotations

import wx

from lab4 import cases
from lab4.dynamic_student import make_student
from lab4.inspector import describe
from ui.cases import CasePanel
from ui.theme import PAGE_BG, apply_window_icon, make_header


class Lab4Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="Lab 4", size=(780, 480))
        apply_window_icon(self)
        self.student = make_student()

        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "Lab 4  Reflection"), 0, wx.EXPAND)

        body = wx.BoxSizer(wx.HORIZONTAL)
        tree_wrap = wx.Panel(root)
        tree_wrap.SetBackgroundColour(wx.WHITE)
        tree_sizer = wx.BoxSizer(wx.VERTICAL)
        self.tree = wx.TreeCtrl(tree_wrap, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        tree_sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 8)
        tree_wrap.SetSizer(tree_sizer)
        body.Add(tree_wrap, 1, wx.EXPAND | wx.ALL, 8)
        body.Add(
            CasePanel(
                root,
                [
                    ("type() + greet", self._case_greet),
                    ("inspect signature", self._case_sig),
                    ("runtime method", self._case_runtime),
                    ("annotations", cases.annotated),
                    ("Python bridge", self._case_bridge),
                    ("Java bridge", self._case_java),
                ],
            ),
            0,
            wx.EXPAND | wx.ALL,
            8,
        )
        layout.Add(body, 1, wx.EXPAND)
        root.SetSizer(layout)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        self.tree.DeleteAllItems()
        root = self.tree.AddRoot("Student")
        for member in describe(self.student):
            self.tree.AppendItem(root, f"{member.name}{member.signature}")

    def _case_greet(self) -> str:
        text = cases.dynamic_greet(self.student)
        self._refresh_tree()
        return text

    def _case_sig(self) -> str:
        text = cases.signatures(self.student)
        self._refresh_tree()
        return text

    def _case_runtime(self) -> str:
        text = cases.runtime_method(self.student)
        self._refresh_tree()
        return text

    def _case_bridge(self) -> str:
        return cases.python_bridge(self.student)

    def _case_java(self) -> str:
        return cases.java_bridge(self.student)

    def _on_close(self, event: wx.CloseEvent) -> None:
        cases.stop_bridge()
        event.Skip()
