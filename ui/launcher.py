"""Main course launcher with four lab cards."""

from __future__ import annotations

import wx

from configs.cfg import (
    CITY,
    COURSE,
    DEPARTMENT,
    FACULTY,
    STUDENT_NAME,
    STUDENT_ROLE,
    TEACHER_NAME,
    TEACHER_TITLE,
    UNIVERSITY,
    YEAR,
)
from ui.theme import (
    ACCENT,
    MUTED,
    PAGE_BG,
    apply_window_icon,
    make_header,
    styled_button,
)

LAB_CARDS = [
    (
        "01",
        "Сериализация и десериализация",
        "Pickle и JSON, сокеты с length-prefix, передача WebP как байтов или base64, "
        "сериализация визуальной формы.",
        "lab1",
    ),
    (
        "02",
        "Удалённый вызов модулей",
        "XML-RPC сервер и клиент: вызов функций по имени, Java-клиент, сравнение с REST/CGI.",
        "lab2",
    ),
    (
        "03",
        "Компоненты wxPython",
        "Тулбар с иконками и подсказками: изображение, музыка, браузер, Office, календарь, PDF.",
        "lab3",
    ),
    (
        "04",
        "Рефлексия",
        "Динамический класс Student, inspect, методы в runtime, Java→Python мост и аннотации.",
        "lab4",
    ),
]


class LabCard(wx.Panel):
    def __init__(self, parent: wx.Window, number: str, title: str, body: str, lab_id: str) -> None:
        super().__init__(parent)
        self.lab_id = lab_id
        self.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)

        badge = wx.StaticText(self, label=f"ЛР {number}")
        badge.SetForegroundColour(ACCENT)
        badge.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(badge, 0, wx.LEFT | wx.RIGHT | wx.TOP, 16)

        heading = wx.StaticText(self, label=title)
        heading.SetFont(wx.Font(13, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        heading.Wrap(280)
        sizer.Add(heading, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)

        text = wx.StaticText(self, label=body)
        text.SetForegroundColour(MUTED)
        text.Wrap(280)
        sizer.Add(text, 1, wx.LEFT | wx.RIGHT | wx.TOP, 8)

        open_btn = styled_button(self, "Открыть лабораторию")
        open_btn.Bind(wx.EVT_BUTTON, self._on_open)
        sizer.Add(open_btn, 0, wx.ALL | wx.EXPAND, 16)
        self.SetSizer(sizer)

    def _on_open(self, _event: wx.Event) -> None:
        frame = wx.GetTopLevelParent(self)
        if isinstance(frame, LauncherFrame):
            frame.open_lab(self.lab_id)


class LauncherFrame(wx.Frame):
    def __init__(self) -> None:
        super().__init__(None, title=COURSE, size=(980, 720))
        apply_window_icon(self)
        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, COURSE), 0, wx.EXPAND)

        info = wx.StaticText(
            root,
            label=(
                f"{UNIVERSITY}\n{FACULTY}  ·  {DEPARTMENT}\n"
                f"Выполнил: {STUDENT_NAME}, {STUDENT_ROLE}\n"
                f"Проверил: {TEACHER_NAME}, {TEACHER_TITLE}\n"
                f"{CITY}, {YEAR}"
            ),
        )
        info.SetForegroundColour(wx.Colour(40, 52, 68))
        layout.Add(info, 0, wx.ALL, 18)

        grid = wx.GridSizer(rows=2, cols=2, vgap=14, hgap=14)
        for number, title, body, lab_id in LAB_CARDS:
            grid.Add(LabCard(root, number, title, body, lab_id), 1, wx.EXPAND)
        layout.Add(grid, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 18)

        root.SetSizer(layout)
        self._create_menu()
        self.CreateStatusBar()
        self.SetStatusText("Выберите лабораторную работу")
        self.Centre()

    def _create_menu(self) -> None:
        menubar = wx.MenuBar()
        labs = wx.Menu()
        for idx, (_number, title, _body, lab_id) in enumerate(LAB_CARDS, start=1):
            item = labs.Append(wx.ID_ANY, f"ЛР{idx}. {title}")
            self.Bind(wx.EVT_MENU, lambda _e, lab=lab_id: self.open_lab(lab), item)
        menubar.Append(labs, "Лабораторные")

        help_menu = wx.Menu()
        about = help_menu.Append(wx.ID_ABOUT, "О программе")
        self.Bind(wx.EVT_MENU, self._on_about, about)
        menubar.Append(help_menu, "Справка")
        self.SetMenuBar(menubar)

    def _on_about(self, _event: wx.Event) -> None:
        wx.MessageBox(
            f"{COURSE}\n\n{STUDENT_NAME}, {STUDENT_ROLE}\n"
            f"Преподаватель: {TEACHER_NAME}\n{UNIVERSITY}\n{CITY} {YEAR}",
            "О программе",
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
        elif lab_id == "lab3":
            from lab3.app import Lab3Frame

            Lab3Frame(self).Show()
        elif lab_id == "lab4":
            from lab4.gui import Lab4Frame

            Lab4Frame(self).Show()
        self.SetStatusText(f"Открыта {lab_id}")


def run_launcher() -> None:
    app = wx.GetApp() or wx.App(False)
    frame = LauncherFrame()
    frame.Show()
    app.MainLoop()
