"""Compact wx lab: toolbar + cases that drive each tool."""

from __future__ import annotations

from datetime import datetime

import wx
import wx.adv
import wx.html2

from configs.cfg import SAMPLES_DIR
from helpers.images import bytes_to_wx_bitmap, load_icon
from helpers.office import open_calendar, open_excel, open_path, open_word, play_audio, stop_audio
from lab3.actions import extract_pdf_text
from lab3.widgets import CustomButton
from ui.cases import CasePanel
from ui.theme import PAGE_BG, apply_window_icon, make_header

ID_IMAGE = wx.NewIdRef()
ID_MUSIC = wx.NewIdRef()
ID_BROWSER = wx.NewIdRef()
ID_WORD = wx.NewIdRef()
ID_EXCEL = wx.NewIdRef()
ID_CALENDAR = wx.NewIdRef()
ID_PDF = wx.NewIdRef()


class Lab3Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="Lab 3", size=(980, 620))
        apply_window_icon(self)

        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "Lab 3  wxPython"), 0, wx.EXPAND)
        layout.Add(self._toolbar(root), 0, wx.EXPAND)

        body = wx.BoxSizer(wx.HORIZONTAL)
        body.Add(self._stage(root), 1, wx.EXPAND | wx.ALL, 8)
        body.Add(
            CasePanel(
                root,
                [
                    ("WebP image", self._case_image),
                    ("music", self._case_music),
                    ("Google browser", self._case_browser),
                    ("calendar + clock", self._case_calendar),
                    ("PDF", self._case_pdf),
                    ("Word / Pages", self._case_word),
                    ("Excel / Numbers", self._case_excel),
                    ("CustomButton", self._case_custom),
                ],
            ),
            0,
            wx.EXPAND | wx.ALL,
            8,
        )
        layout.Add(body, 1, wx.EXPAND)
        root.SetSizer(layout)

        self.clock_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_clock, self.clock_timer)
        self.clock_timer.Start(500)
        self.Bind(wx.EVT_CLOSE, self._on_close)

    def _toolbar(self, parent: wx.Window) -> wx.ToolBar:
        bar = wx.ToolBar(parent, style=wx.TB_HORIZONTAL | wx.TB_TEXT | wx.TB_FLAT)
        bar.SetToolBitmapSize(wx.Size(32, 32))
        for tool_id, label, icon, hint in (
            (ID_IMAGE, "Photo", "image", "Image"),
            (ID_MUSIC, "Music", "music", "Audio"),
            (ID_BROWSER, "Google", "browser", "WebView"),
            (ID_WORD, "Word", "word", "Word / Pages"),
            (ID_EXCEL, "Excel", "excel", "Excel / Numbers"),
            (ID_CALENDAR, "Calendar", "calendar", "Calendar"),
            (ID_PDF, "PDF", "pdf", "PDF"),
        ):
            bar.AddTool(int(tool_id), label, load_icon(icon), hint)
        bar.Realize()
        bar.Bind(wx.EVT_TOOL, self._on_tool)
        return bar

    def _stage(self, parent: wx.Window) -> wx.Panel:
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.image_view = wx.StaticBitmap(panel, size=(420, 200))
        sizer.Add(self.image_view, 0, wx.ALL, 8)
        self.clock_label = wx.StaticText(panel, label="--:--:--")
        self.clock_label.SetFont(wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(self.clock_label, 0, wx.LEFT, 8)
        self.calendar = wx.adv.CalendarCtrl(panel)
        sizer.Add(self.calendar, 0, wx.ALL, 8)
        self.custom = CustomButton(panel, "CustomButton", "wx.Button subclass")
        self.custom.Bind(wx.EVT_BUTTON, lambda _e: None)
        sizer.Add(self.custom, 0, wx.ALL, 8)
        try:
            self.browser = wx.html2.WebView.New(panel)
        except Exception:
            self.browser = None
        if self.browser is not None:
            sizer.Add(self.browser, 1, wx.EXPAND | wx.ALL, 4)
        self.pdf_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 80))
        sizer.Add(self.pdf_text, 0, wx.EXPAND | wx.ALL, 8)
        panel.SetSizer(sizer)
        return panel

    def _on_clock(self, _event: wx.TimerEvent) -> None:
        self.clock_label.SetLabel(datetime.now().strftime("%H:%M:%S"))

    def _on_tool(self, event: wx.CommandEvent) -> None:
        mapping = {
            int(ID_IMAGE): self._case_image,
            int(ID_MUSIC): self._case_music,
            int(ID_BROWSER): self._case_browser,
            int(ID_WORD): self._case_word,
            int(ID_EXCEL): self._case_excel,
            int(ID_CALENDAR): self._case_calendar,
            int(ID_PDF): self._case_pdf,
        }
        try:
            mapping[event.GetId()]()
        except Exception as exc:
            wx.Bell()
            wx.LogError(str(exc))

    def _case_image(self) -> str:
        path = SAMPLES_DIR / "avatar.webp"
        if not path.exists():
            raise FileNotFoundError(path)
        self.image_view.SetBitmap(bytes_to_wx_bitmap(path.read_bytes(), (420, 200)))
        self.Layout()
        return path.name

    def _case_music(self) -> str:
        path = SAMPLES_DIR / "sample.wav"
        backend = play_audio(path)
        return f"{backend} {path.name}"

    def _case_browser(self) -> str:
        if self.browser is None:
            open_path("https://www.google.com")
            return "system browser"
        self.browser.LoadURL("https://www.google.com")
        return "WebView"

    def _case_calendar(self) -> str:
        self.calendar.SetFocus()
        try:
            open_calendar()
        except Exception:
            pass
        if ":" not in self.clock_label.GetLabel():
            raise AssertionError("clock")
        return "calendar+clock"

    def _case_pdf(self) -> str:
        path = SAMPLES_DIR / "sample.pdf"
        text = extract_pdf_text(path)
        self.pdf_text.SetValue(text)
        open_path(path)
        if "BSUIR" not in text and "Component" not in text:
            raise AssertionError(text[:80])
        return f"{len(text)} chars"

    def _case_word(self) -> str:
        sample = SAMPLES_DIR / "sample.rtf"
        return open_word(sample if sample.exists() else None)

    def _case_excel(self) -> str:
        sample = SAMPLES_DIR / "sample.csv"
        return open_excel(sample if sample.exists() else None)

    def _case_custom(self) -> str:
        if not isinstance(self.custom, wx.Button):
            raise AssertionError(type(self.custom))
        return self.custom.GetLabel()

    def _on_close(self, event: wx.CloseEvent) -> None:
        self.clock_timer.Stop()
        stop_audio()
        event.Skip()
