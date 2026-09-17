"""Checklist of short runnable cases for a lab window."""

from __future__ import annotations

from collections.abc import Callable

import wx

from ui.theme import MUTED, append_log, make_log, styled_button

CaseFn = Callable[[], str]


class CasePanel(wx.Panel):
    def __init__(self, parent: wx.Window, cases: list[tuple[str, CaseFn]]) -> None:
        super().__init__(parent)
        self.SetBackgroundColour(wx.WHITE)
        self._cases = cases
        self._ok = [False] * len(cases)

        sizer = wx.BoxSizer(wx.VERTICAL)
        caption = wx.StaticText(self, label="Cases")
        caption.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(caption, 0, wx.LEFT | wx.TOP | wx.RIGHT, 10)

        self.list = wx.ListBox(self, choices=[title for title, _fn in cases])
        if cases:
            self.list.SetSelection(0)
        sizer.Add(self.list, 1, wx.EXPAND | wx.ALL, 8)

        row = wx.BoxSizer(wx.HORIZONTAL)
        run_one = styled_button(self, "Run")
        run_all = styled_button(self, "All", primary=False)
        run_one.Bind(wx.EVT_BUTTON, self._on_run)
        run_all.Bind(wx.EVT_BUTTON, self._on_run_all)
        row.Add(run_one, 1, wx.RIGHT, 6)
        row.Add(run_all, 1)
        sizer.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        self.status = wx.StaticText(self, label=f"0/{len(cases)}")
        self.status.SetForegroundColour(MUTED)
        sizer.Add(self.status, 0, wx.ALL, 8)

        self.log = make_log(self, height=110)
        sizer.Add(self.log, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.SetSizer(sizer)
        self.SetMinSize((240, -1))

    def _on_run(self, _event: wx.Event) -> None:
        index = self.list.GetSelection()
        if index == wx.NOT_FOUND:
            return
        self.run_index(index)

    def _on_run_all(self, _event: wx.Event) -> None:
        self.log.Clear()
        for index in range(len(self._cases)):
            self.run_index(index)

    def run_index(self, index: int) -> None:
        title, func = self._cases[index]
        try:
            detail = func()
        except Exception as exc:
            self._ok[index] = False
            self._relabel(index, title, ok=False)
            append_log(self.log, f"FAIL  {title}: {exc}")
        else:
            self._ok[index] = True
            self._relabel(index, title, ok=True)
            append_log(self.log, f"OK    {title}" + (f" — {detail}" if detail else ""))
        done = sum(self._ok)
        self.status.SetLabel(f"{done}/{len(self._cases)}")
        self.list.SetSelection(index)

    def _relabel(self, index: int, title: str, ok: bool) -> None:
        mark = "✓" if ok else "✗"
        self.list.SetString(index, f"{mark}  {title}")
