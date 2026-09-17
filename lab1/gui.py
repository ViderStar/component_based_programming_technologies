"""Compact lab 1 window: student card + runnable cases."""

from __future__ import annotations

from pathlib import Path

import wx

from configs.cfg import DEFAULT_STUDENT, SAMPLES_DIR
from helpers.images import bytes_to_wx_bitmap
from lab1 import cases
from lab1.codecs import attach_photo
from lab1.gui_form import VisualFormFrame
from lab1.models import Student
from ui.cases import CasePanel
from ui.theme import PAGE_BG, apply_window_icon, make_header, styled_button


class Lab1Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="Lab 1", size=(860, 520))
        apply_window_icon(self)
        self.photo_path: Path | None = SAMPLES_DIR / "avatar.webp"
        if self.photo_path and not self.photo_path.exists():
            self.photo_path = None

        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "Lab 1  Serialization"), 0, wx.EXPAND)

        body = wx.BoxSizer(wx.HORIZONTAL)
        body.Add(self._workspace(root), 1, wx.EXPAND | wx.ALL, 8)
        self.cases = CasePanel(
            root,
            [
                ("pickle + WebP", self._case_pickle),
                ("JSON base64", self._case_json),
                ("other process", self._case_reader),
                ("TCP pickle", lambda: self._case_tcp("pickle")),
                ("TCP JSON", lambda: self._case_tcp("json")),
                ("GUI form", self._case_form),
            ],
        )
        body.Add(self.cases, 0, wx.EXPAND | wx.ALL, 8)
        layout.Add(body, 1, wx.EXPAND)
        root.SetSizer(layout)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self._refresh_preview()

    def _workspace(self, parent: wx.Window) -> wx.Panel:
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(0, 2, 6, 6)
        grid.AddGrowableCol(1, 1)
        self.name_ctrl = wx.TextCtrl(panel, value=DEFAULT_STUDENT["name"])
        self.group_ctrl = wx.TextCtrl(panel, value=DEFAULT_STUDENT["group"])
        self.faculty_ctrl = wx.TextCtrl(panel, value=DEFAULT_STUDENT["faculty"])
        for label, ctrl in (("Name", self.name_ctrl), ("Group", self.group_ctrl), ("Faculty", self.faculty_ctrl)):
            grid.Add(wx.StaticText(panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(ctrl, 1, wx.EXPAND)
        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 10)
        photo_btn = styled_button(panel, "Photo…", primary=False)
        photo_btn.Bind(wx.EVT_BUTTON, self._on_pick_photo)
        sizer.Add(photo_btn, 0, wx.LEFT | wx.RIGHT, 10)
        self.preview = wx.StaticBitmap(panel, size=(280, 200))
        sizer.Add(self.preview, 0, wx.ALL, 10)
        panel.SetSizer(sizer)
        return panel

    def _student(self) -> Student:
        student = Student(
            name=self.name_ctrl.GetValue().strip(),
            group=self.group_ctrl.GetValue().strip(),
            faculty=self.faculty_ctrl.GetValue().strip(),
        )
        if self.photo_path and self.photo_path.exists():
            attach_photo(student, self.photo_path)
        return cases.sample_student(student)

    def _apply(self, student: Student) -> None:
        self.name_ctrl.SetValue(student.name)
        self.group_ctrl.SetValue(student.group)
        self.faculty_ctrl.SetValue(student.faculty)
        if student.photo is not None:
            from configs.cfg import ARTIFACTS_DIR

            target = ARTIFACTS_DIR / student.photo.filename
            target.write_bytes(student.photo.data)
            self.photo_path = target
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        if not self.photo_path or not self.photo_path.exists():
            return
        self.preview.SetBitmap(bytes_to_wx_bitmap(self.photo_path.read_bytes(), (280, 200)))
        self.Layout()

    def _on_pick_photo(self, _event: wx.Event) -> None:
        dialog = wx.FileDialog(
            self,
            "Photo",
            wildcard="Images|*.webp;*.png;*.jpg;*.jpeg",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.photo_path = Path(dialog.GetPath())
            self._refresh_preview()

    def _case_pickle(self) -> str:
        return cases.pickle_file(self._student())

    def _case_json(self) -> str:
        return cases.json_base64(self._student())

    def _case_reader(self) -> str:
        return cases.other_app_reader(self._student())

    def _case_tcp(self, fmt: str) -> str:
        student = self._student()
        echoed = None

        def grab(item: Student, _fmt: str) -> None:
            nonlocal echoed
            echoed = item

        server = cases.ensure_server()
        server.on_student = grab
        detail = cases.tcp_roundtrip(student, fmt)
        if echoed is not None:
            wx.CallAfter(self._apply, echoed)
        return detail

    def _case_form(self) -> str:
        state = cases.gui_form(self._student())
        VisualFormFrame(self, state).Show()
        return state.title

    def _on_close(self, event: wx.CloseEvent) -> None:
        cases.stop_server()
        event.Skip()
