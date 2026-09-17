"""wxPython multimedia workstation: toolbar, browser, calendar, PDF, office."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import wx
import wx.adv
import wx.html2

from configs.cfg import SAMPLES_DIR
from helpers.images import bytes_to_wx_bitmap, load_icon
from helpers.office import open_calendar, open_excel, open_path, open_word, play_audio, stop_audio
from lab3.actions import extract_pdf_text
from lab3.widgets import CustomButton
from ui.theme import PAGE_BG, append_log, apply_window_icon, make_header, make_log

ID_IMAGE = wx.NewIdRef()
ID_MUSIC = wx.NewIdRef()
ID_BROWSER = wx.NewIdRef()
ID_WORD = wx.NewIdRef()
ID_EXCEL = wx.NewIdRef()
ID_CALENDAR = wx.NewIdRef()
ID_PDF = wx.NewIdRef()


class Lab3Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="ЛР3 · Компоненты wxPython", size=(1100, 780))
        apply_window_icon(self)
        self._music_path: Path | None = None

        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "ЛР3  Тулбар, браузер, календарь, PDF, Office"), 0, wx.EXPAND)
        layout.Add(self._build_toolbar(root), 0, wx.EXPAND)

        split = wx.BoxSizer(wx.HORIZONTAL)
        split.Add(self._build_left(root), 1, wx.EXPAND | wx.ALL, 10)
        split.Add(self._build_right(root), 1, wx.EXPAND | wx.ALL, 10)
        layout.Add(split, 1, wx.EXPAND)

        self.log = make_log(root, height=140)
        layout.Add(self.log, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        root.SetSizer(layout)

        self.clock_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_clock, self.clock_timer)
        self.clock_timer.Start(500)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        append_log(self.log, "Наведите курсор на иконки тулбара — появится подсказка.")

    def _build_toolbar(self, parent: wx.Window) -> wx.Panel:
        holder = wx.Panel(parent)
        holder.SetBackgroundColour(wx.WHITE)
        toolbar = wx.ToolBar(holder, style=wx.TB_HORIZONTAL | wx.TB_TEXT | wx.TB_FLAT)
        toolbar.SetToolBitmapSize(wx.Size(32, 32))
        tools = [
            (ID_IMAGE, "Изображение", "image", "Загрузить и показать изображение"),
            (ID_MUSIC, "Музыка", "music", "Загрузить и проиграть аудиофайл"),
            (ID_BROWSER, "Браузер", "browser", "Открыть Google во встроенном WebView"),
            (ID_WORD, "Word", "word", "Открыть Word / Pages / TextEdit"),
            (ID_EXCEL, "Excel", "excel", "Открыть Excel / Numbers"),
            (ID_CALENDAR, "Календарь", "calendar", "Показать календарь и системные часы"),
            (ID_PDF, "PDF", "pdf", "Прочитать PDF и открыть в системном просмотрщике"),
        ]
        for tool_id, label, icon, hint in tools:
            toolbar.AddTool(int(tool_id), label, load_icon(icon), hint)
        toolbar.Realize()
        toolbar.Bind(wx.EVT_TOOL, self._on_tool)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(toolbar, 0, wx.EXPAND)
        holder.SetSizer(sizer)
        self.toolbar = toolbar
        return holder

    def _build_left(self, parent: wx.Window) -> wx.Panel:
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.image_view = wx.StaticBitmap(panel, size=(480, 280))
        sizer.Add(self.image_view, 0, wx.ALL, 8)

        self.clock_label = wx.StaticText(panel, label="--:--:--")
        self.clock_label.SetFont(wx.Font(22, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(self.clock_label, 0, wx.ALL, 8)

        self.calendar = wx.adv.CalendarCtrl(panel)
        sizer.Add(self.calendar, 0, wx.ALL, 8)

        demo = CustomButton(panel, "Кастомная кнопка wx.Button", "Это CustomButton из методички")
        demo.Bind(wx.EVT_BUTTON, lambda _e: append_log(self.log, "CustomButton: клик"))
        sizer.Add(demo, 0, wx.ALL, 8)
        panel.SetSizer(sizer)
        return panel

    def _build_right(self, parent: wx.Window) -> wx.Panel:
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        try:
            self.browser = wx.html2.WebView.New(panel)
            self.browser.LoadURL("https://www.google.com")
        except Exception as exc:  # pragma: no cover - depends on OS webview
            self.browser = None
            fallback = wx.StaticText(panel, label=f"WebView недоступен: {exc}")
            sizer.Add(fallback, 0, wx.ALL, 8)
        if self.browser is not None:
            sizer.Add(self.browser, 1, wx.EXPAND | wx.ALL, 4)
        self.pdf_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 180))
        sizer.Add(self.pdf_text, 0, wx.EXPAND | wx.ALL, 8)
        panel.SetSizer(sizer)
        return panel

    def _on_clock(self, _event: wx.TimerEvent) -> None:
        self.clock_label.SetLabel(datetime.now().strftime("%H:%M:%S  %d.%m.%Y"))

    def _on_tool(self, event: wx.CommandEvent) -> None:
        tool_id = event.GetId()
        if tool_id == int(ID_IMAGE):
            self._open_image()
        elif tool_id == int(ID_MUSIC):
            self._open_music()
        elif tool_id == int(ID_BROWSER):
            self._open_browser()
        elif tool_id == int(ID_WORD):
            self._open_word()
        elif tool_id == int(ID_EXCEL):
            self._open_excel()
        elif tool_id == int(ID_CALENDAR):
            self._focus_calendar()
        elif tool_id == int(ID_PDF):
            self._open_pdf()

    def _open_image(self) -> None:
        path = self._pick_file("Изображение", "Images|*.png;*.jpg;*.jpeg;*.webp;*.bmp")
        if not path:
            return
        self.image_view.SetBitmap(bytes_to_wx_bitmap(path.read_bytes(), (480, 280)))
        self.Layout()
        append_log(self.log, f"Изображение: {path}")

    def _open_music(self) -> None:
        path = self._pick_file("Аудио", "Audio|*.wav;*.mp3;*.ogg")
        if not path:
            return
        backend = play_audio(path)
        self._music_path = path
        append_log(self.log, f"Музыка через {backend}: {path.name}")

    def _open_browser(self) -> None:
        if self.browser is None:
            open_path("https://www.google.com")
            append_log(self.log, "Встроенный браузер недоступен, открыт системный.")
            return
        self.browser.LoadURL("https://www.google.com")
        append_log(self.log, "WebView: https://www.google.com")

    def _open_word(self) -> None:
        sample = SAMPLES_DIR / "sample.rtf"
        used = open_word(sample if sample.exists() else None)
        append_log(self.log, f"Текстовый процессор: {used}")

    def _open_excel(self) -> None:
        sample = SAMPLES_DIR / "sample.csv"
        used = open_excel(sample if sample.exists() else None)
        append_log(self.log, f"Таблицы: {used}")

    def _focus_calendar(self) -> None:
        self.calendar.SetFocus()
        try:
            used = open_calendar()
            append_log(self.log, f"Системный календарь: {used}. Встроенные часы тикают сверху.")
        except Exception as exc:
            append_log(self.log, f"Системный календарь: {exc}. Используйте виджет в окне.")

    def _open_pdf(self) -> None:
        default = SAMPLES_DIR / "sample.pdf"
        path = default if default.exists() else self._pick_file("PDF", "PDF|*.pdf")
        if not path:
            return
        text = extract_pdf_text(path)
        self.pdf_text.SetValue(text)
        open_path(path)
        append_log(self.log, f"PDF: извлечён текст ({len(text)} символов) и открыт просмотрщик")

    def _pick_file(self, title: str, wildcard: str) -> Path | None:
        start = str(SAMPLES_DIR) if SAMPLES_DIR.exists() else ""
        dialog = wx.FileDialog(self, title, defaultDir=start, wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() != wx.ID_OK:
            return None
        return Path(dialog.GetPath())

    def _on_close(self, event: wx.CloseEvent) -> None:
        self.clock_timer.Stop()
        stop_audio()
        event.Skip()
