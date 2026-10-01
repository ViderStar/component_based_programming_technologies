"""Lab 2 window: keypad calculator, COM object inspector and HTML client, all backed by one COM class."""

from __future__ import annotations

from collections.abc import Callable

import wx
import wx.html2
from wx.lib.buttons import GenButton

from helpers.office import open_excel, open_path
from lab2 import cases, registry
from lab2.calculator import Calculator
from lab2.client import ComError, Dispatch, DispatchProxy
from ui.cases import CasePanel
from ui.theme import ACCENT, BSUIR_BLUE, MUTED, PAGE_BG, append_log, apply_window_icon, make_header, make_log, styled_button

KEYS = [
    ["C", "±", "⌫", "÷"],
    ["7", "8", "9", "×"],
    ["4", "5", "6", "−"],
    ["1", "2", "3", "+"],
    ["0", ".", "^", "="],
]
OPERATIONS = {"+": "Add", "−": "Sub", "×": "Mul", "÷": "Div", "^": "Pow"}
KEYBOARD = {"*": "×", "/": "÷", "-": "−", "\r": "=", "\x08": "⌫", "\x1b": "C", ",": "."}


def _number(text: str) -> float | int:
    value = float(text)
    return int(value) if value.is_integer() else value


def _format(value: float | int) -> str:
    return f"{value:.12g}"


class CalculatorPanel(wx.Panel):
    """Immediate-execution keypad; every operation is delegated to `invoke(method, a, b)`."""

    def __init__(self, parent: wx.Window, invoke: Callable[[str, float | int, float | int], float | int]) -> None:
        super().__init__(parent)
        self.SetBackgroundColour(wx.WHITE)
        self._invoke = invoke
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.history = wx.StaticText(self, label=" ", style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE)
        self.history.SetForegroundColour(MUTED)
        sizer.Add(self.history, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 12)
        self.display = wx.TextCtrl(self, value="0", style=wx.TE_READONLY | wx.TE_RIGHT)
        self.display.SetFont(wx.Font(28, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(self.display, 0, wx.EXPAND | wx.ALL, 12)

        grid = wx.GridSizer(rows=len(KEYS), cols=4, vgap=6, hgap=6)
        for row in KEYS:
            for key in row:
                button = GenButton(self, label=key, size=(64, 44), style=wx.BORDER_NONE)
                button.SetUseFocusIndicator(False)
                button.SetFont(wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                if key == "=":
                    button.SetBackgroundColour(ACCENT)
                    button.SetForegroundColour(wx.WHITE)
                elif key in OPERATIONS:
                    button.SetBackgroundColour(BSUIR_BLUE)
                    button.SetForegroundColour(wx.WHITE)
                else:
                    button.SetBackgroundColour(PAGE_BG)
                button.Bind(wx.EVT_BUTTON, lambda _e, k=key: self.press(k))
                grid.Add(button, 1, wx.EXPAND)
        sizer.Add(grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.clear()

    def clear(self) -> None:
        self._entry = "0"
        self._left: float | int | None = None
        self._op: str | None = None
        self._fresh = True
        self.history.SetLabel(" ")
        self.display.SetValue("0")

    def press(self, key: str) -> None:
        if key == "C":
            self.clear()
        elif key in OPERATIONS:
            if self._op is not None and not self._fresh and not self._evaluate():
                return
            self._left, self._op, self._fresh = _number(self._entry), key, True
            self.history.SetLabel(f"{_format(self._left)} {key}")
        elif key == "=":
            if self._op is not None:
                self._evaluate()
        else:
            self._edit(key)
            self.display.SetValue(self._entry)

    def _edit(self, key: str) -> None:
        if key == "±":
            if self._entry != "0":
                self._entry = self._entry[1:] if self._entry.startswith("-") else "-" + self._entry
        elif key == "⌫":
            if not self._fresh:
                self._entry = self._entry[:-1]
                if self._entry in ("", "-"):
                    self._entry = "0"
        elif key == ".":
            if self._fresh:
                self._entry = "0."
            elif "." not in self._entry:
                self._entry += "."
            self._fresh = False
        else:
            self._entry = key if self._fresh or self._entry == "0" else self._entry + key
            self._fresh = False

    def _evaluate(self) -> bool:
        left, op, right = self._left, self._op, _number(self._entry)
        self.clear()
        try:
            result = self._invoke(OPERATIONS[op], left, right)
        except ComError as exc:
            self.history.SetLabel(str(exc))
            self.display.SetValue("Error")
            return False
        self._entry = _format(result)
        self.history.SetLabel(f"{_format(left)} {op} {_format(right)} =")
        self.display.SetValue(self._entry)
        return True

    def _on_key(self, event: wx.KeyEvent) -> None:
        char = chr(event.GetUnicodeKey()) if event.GetUnicodeKey() else ""
        if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            char = "\r"
        if event.ShiftDown() and char in ("=", "8", "6"):
            char = {"=": "+", "8": "*", "6": "^"}[char]
        key = KEYBOARD.get(char, char)
        if key and any(key in row for row in KEYS):
            self.press(key)
        else:
            event.Skip()


class Lab2Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="Lab 2", size=(1000, 700))
        apply_window_icon(self)
        self.calc: DispatchProxy | None = None

        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "Lab 2  COM server"), 0, wx.EXPAND)

        body = wx.BoxSizer(wx.HORIZONTAL)
        left = wx.BoxSizer(wx.VERTICAL)
        self.book = wx.Notebook(root)
        self.keypad = CalculatorPanel(self.book, self._invoke)
        self.book.AddPage(self.keypad, "Calculator")
        self.book.AddPage(self._com_page(self.book), "COM object")
        self.book.AddPage(self._html_page(self.book), "HTML client")
        self.book.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_page)
        left.Add(self.book, 1, wx.EXPAND)
        self.trace_log = make_log(root, height=150)
        left.Add(self.trace_log, 0, wx.EXPAND | wx.TOP, 8)
        body.Add(left, 1, wx.EXPAND | wx.ALL, 8)

        self.cases = CasePanel(
            root,
            [
                ("register", self._refreshing(cases.register)),
                ("registry keys", self._refreshing(cases.registry_keys)),
                ("Dispatch: local server", self._refreshing(lambda: cases.dispatch(self._trace))),
                ("Add Sub Mul Div Pow", self._refreshing(lambda: cases.arithmetic(self._trace))),
                ("COM errors", self._refreshing(lambda: cases.com_errors(self._trace))),
                ("keypad 12 × 12 =", self._case_keypad),
                ("Excel client", self._case_excel),
                ("HTML client", self._case_html),
                ("unregister", self._refreshing(cases.unregister)),
            ],
        )
        body.Add(self.cases, 0, wx.EXPAND | wx.ALL, 8)
        layout.Add(body, 1, wx.EXPAND)
        root.SetSizer(layout)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        self._trace(cases.register())
        self._refresh()

    def _com_page(self, parent: wx.Window) -> wx.Panel:
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        row = wx.BoxSizer(wx.HORIZONTAL)
        for label, handler, primary in (
            ("Register", self._on_register, True),
            ("Unregister", self._on_unregister, False),
            ("Dispatch", self._on_dispatch, True),
            ("Release", self._on_release, False),
        ):
            button = styled_button(panel, label, primary=primary)
            button.Bind(wx.EVT_BUTTON, handler)
            row.Add(button, 1, wx.RIGHT, 6)
        sizer.Add(row, 0, wx.EXPAND | wx.ALL, 10)
        self.status = wx.StaticText(panel, label="")
        self.status.SetForegroundColour(MUTED)
        sizer.Add(self.status, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.registry_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.BORDER_SIMPLE)
        self.registry_list.InsertColumn(0, "Key", width=330)
        self.registry_list.InsertColumn(1, "Value", width=420)
        sizer.Add(self.registry_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        methods = ", ".join(Calculator._public_methods_)
        sizer.Add(wx.StaticText(panel, label=f"_public_methods_: {methods}"), 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        panel.SetSizer(sizer)
        return panel

    def _html_page(self, parent: wx.Window) -> wx.Panel:
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        row = wx.BoxSizer(wx.HORIZONTAL)
        self.url_label = wx.StaticText(panel, label="")
        row.Add(self.url_label, 1, wx.ALIGN_CENTER_VERTICAL)
        external = styled_button(panel, "Open in browser", primary=False)
        external.Bind(wx.EVT_BUTTON, lambda _e: open_path(self._load_page()))
        row.Add(external, 0)
        sizer.Add(row, 0, wx.EXPAND | wx.ALL, 10)
        try:
            self.browser = wx.html2.WebView.New(panel)
        except Exception:
            self.browser = None
        if self.browser is not None:
            sizer.Add(self.browser, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        panel.SetSizer(sizer)
        return panel

    def _trace(self, line: str) -> None:
        append_log(self.trace_log, line)

    def _refresh(self) -> None:
        self.registry_list.DeleteAllItems()
        for key, value in registry.entries().items():
            self.registry_list.Append((key, value))
        registered = registry.query(rf"HKCR\{cases.PROGID}\CLSID") is not None
        server = f"server pid {self.calc.pid}" if self.calc is not None else "no object"
        self.status.SetLabel(f"{cases.PROGID}: {'registered' if registered else 'not registered'}  ·  {server}")

    def _refreshing(self, case: Callable[[], str]) -> Callable[[], str]:
        def run() -> str:
            try:
                return case()
            finally:
                self._refresh()

        return run

    def _object(self) -> DispatchProxy:
        if self.calc is None:
            self.calc = Dispatch(cases.PROGID, self._trace)
            self._refresh()
        return self.calc

    def _invoke(self, method: str, a: float | int, b: float | int) -> float | int:
        return getattr(self._object(), method)(a, b)

    def _load_page(self) -> str:
        url = cases.ensure_web().url
        self.url_label.SetLabel(url)
        if self.browser is not None:
            self.browser.LoadURL(url)
        return url

    def _on_page(self, event: wx.BookCtrlEvent) -> None:
        if event.GetSelection() == 2:
            try:
                self._load_page()
            except OSError as exc:
                self._trace(f"web server: {exc}")
        event.Skip()

    def _on_register(self, _event: wx.Event) -> None:
        self._trace(cases.register())
        self._refresh()

    def _on_unregister(self, _event: wx.Event) -> None:
        self._trace(f"unregister: {registry.unregister(Calculator)} keys removed")
        self._refresh()

    def _on_dispatch(self, _event: wx.Event) -> None:
        try:
            self._object()
        except ComError as exc:
            self._trace(f'Dispatch("{cases.PROGID}") -> {exc}')

    def _on_release(self, _event: wx.Event) -> None:
        if self.calc is not None:
            self.calc.Release()
            self.calc = None
        self._refresh()

    def _case_keypad(self) -> str:
        cases.register()
        self.book.ChangeSelection(0)
        self.keypad.clear()
        for key in ("1", "2", "×", "1", "2", "="):
            self.keypad.press(key)
        shown = self.keypad.display.GetValue()
        if shown != "144":
            raise AssertionError(f"{shown}: {self.keypad.history.GetLabel()}")
        return f"display {shown}, server pid {self._object().pid}"

    def _case_excel(self) -> str:
        detail = cases.excel_sheet(self._trace)
        return f"{detail}, opened in {open_excel(cases.EXCEL_CSV)}"

    def _case_html(self) -> str:
        detail = cases.html_client()
        self._load_page()
        return detail

    def _on_close(self, event: wx.CloseEvent) -> None:
        if self.calc is not None:
            self.calc.Release()
            self.calc = None
        cases.stop_web()
        event.Skip()
