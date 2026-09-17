"""wxPython workbench for serialization, files, sockets, and GUI-form snapshots."""

from __future__ import annotations

from pathlib import Path

import wx

from configs.cfg import ARTIFACTS_DIR, DEFAULT_STUDENT, LAB1_HOST, LAB1_PORT, SAMPLES_DIR
from helpers.images import bytes_to_wx_bitmap
from helpers.paths import ensure_artifacts_dir
from lab1.client import send_student
from lab1.codecs import attach_photo, dumps_json, dumps_pickle, loads_json_form, loads_json_student, loads_pickle
from lab1.models import GuiFormState, Student
from lab1.server import StudentServer
from ui.theme import PAGE_BG, append_log, apply_window_icon, make_header, make_log, styled_button


class VisualFormFrame(wx.Frame):
    def __init__(self, parent: wx.Window | None, state: GuiFormState) -> None:
        super().__init__(parent, title=state.title, size=(420, 240))
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.label = wx.StaticText(panel, label=state.label_text)
        self.text = wx.TextCtrl(panel, value=state.text_value)
        self.button = wx.Button(panel, label=state.button_label)
        self.button.Bind(wx.EVT_BUTTON, self._on_click)
        sizer.Add(self.label, 0, wx.ALL, 12)
        sizer.Add(self.text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        sizer.Add(self.button, 0, wx.ALL, 12)
        panel.SetSizer(sizer)
        self.state = state

    def _on_click(self, _event: wx.Event) -> None:
        self.label.SetLabel(f"Кнопка нажата: {self.text.GetValue() or 'пусто'}")
        self.state.label_text = self.label.GetLabel()
        self.state.text_value = self.text.GetValue()

    def snapshot(self) -> GuiFormState:
        return GuiFormState(
            title=self.GetTitle(),
            button_label=self.button.GetLabel(),
            text_value=self.text.GetValue(),
            label_text=self.label.GetLabel(),
        )


class Lab1Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="ЛР1 · Сериализация / десериализация", size=(1080, 760))
        apply_window_icon(self)
        ensure_artifacts_dir()
        self.server: StudentServer | None = None
        self.photo_path: Path | None = SAMPLES_DIR / "avatar.webp"
        if self.photo_path and not self.photo_path.exists():
            self.photo_path = None

        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "ЛР1  Сериализация объектов и картинок"), 0, wx.EXPAND)

        body = wx.BoxSizer(wx.HORIZONTAL)
        body.Add(self._build_form(root), 1, wx.EXPAND | wx.ALL, 12)
        body.Add(self._build_preview(root), 1, wx.EXPAND | wx.ALL, 12)
        layout.Add(body, 1, wx.EXPAND)

        self.log = make_log(root, height=160)
        layout.Add(self.log, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        root.SetSizer(layout)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self._refresh_preview()
        self._log("Готово. Pickle хранит WebP как байты, JSON — как base64.")

    def _build_form(self, parent: wx.Window) -> wx.Panel:
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.WHITE)
        sizer = wx.FlexGridSizer(rows=0, cols=2, vgap=8, hgap=8)
        sizer.AddGrowableCol(1, 1)

        self.name_ctrl = wx.TextCtrl(panel, value=DEFAULT_STUDENT["name"])
        self.group_ctrl = wx.TextCtrl(panel, value=DEFAULT_STUDENT["group"])
        self.faculty_ctrl = wx.TextCtrl(panel, value=DEFAULT_STUDENT["faculty"])
        for label, ctrl in (
            ("Имя", self.name_ctrl),
            ("Группа", self.group_ctrl),
            ("Факультет", self.faculty_ctrl),
        ):
            sizer.Add(wx.StaticText(panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(ctrl, 1, wx.EXPAND)

        sizer.Add(wx.StaticText(panel, label="Формат"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.fmt = wx.RadioBox(panel, choices=["pickle", "json"], style=wx.RA_SPECIFY_COLS)
        sizer.Add(self.fmt, 0)

        buttons = wx.WrapSizer(wx.HORIZONTAL)
        actions = [
            ("Выбрать WebP / картинку", self._on_pick_photo),
            ("Сохранить в файл", self._on_save),
            ("Загрузить из файла", self._on_load),
            ("Запустить сервер", self._on_start_server),
            ("Остановить сервер", self._on_stop_server),
            ("Отправить по сети", self._on_send),
            ("Сериализовать GUI-форму", self._on_serialize_form),
            ("Восстановить GUI-форму", self._on_restore_form),
        ]
        for label, handler in actions:
            btn = styled_button(panel, label, primary=label.startswith("Отправить") or label.startswith("Сохранить"))
            btn.Bind(wx.EVT_BUTTON, handler)
            buttons.Add(btn, 0, wx.ALL, 4)

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(sizer, 0, wx.EXPAND | wx.ALL, 12)
        outer.Add(buttons, 0, wx.EXPAND | wx.ALL, 8)
        hint = wx.StaticText(
            panel,
            label="Сеть: 4 байта длины (big-endian) + конверт (pickle|json) + полезная нагрузка. "
            "Картинка не режется на 1024 байта.",
        )
        hint.Wrap(480)
        outer.Add(hint, 0, wx.ALL, 12)
        panel.SetSizer(outer)
        return panel

    def _build_preview(self, parent: wx.Window) -> wx.Panel:
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(panel, label="Превью фото (Pillow → wx.Bitmap)"), 0, wx.ALL, 12)
        self.preview = wx.StaticBitmap(panel, size=(320, 240))
        sizer.Add(self.preview, 0, wx.ALL, 12)
        self.photo_info = wx.StaticText(panel, label="Фото не выбрано")
        sizer.Add(self.photo_info, 0, wx.ALL, 12)
        panel.SetSizer(sizer)
        return panel

    def _current_fmt(self) -> str:
        return "pickle" if self.fmt.GetSelection() == 0 else "json"

    def _build_student(self) -> Student:
        student = Student(
            name=self.name_ctrl.GetValue().strip(),
            group=self.group_ctrl.GetValue().strip(),
            faculty=self.faculty_ctrl.GetValue().strip(),
        )
        if self.photo_path and self.photo_path.exists():
            attach_photo(student, self.photo_path)
        return student

    def _apply_student(self, student: Student) -> None:
        self.name_ctrl.SetValue(student.name)
        self.group_ctrl.SetValue(student.group)
        self.faculty_ctrl.SetValue(student.faculty)
        if student.photo is not None:
            target = ARTIFACTS_DIR / student.photo.filename
            target.write_bytes(student.photo.data)
            self.photo_path = target
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        if not self.photo_path or not self.photo_path.exists():
            self.photo_info.SetLabel("Фото не выбрано")
            return
        data = self.photo_path.read_bytes()
        self.preview.SetBitmap(bytes_to_wx_bitmap(data, (320, 240)))
        self.photo_info.SetLabel(
            f"{self.photo_path.name}  ·  {len(data)} байт  ·  {self.photo_path.suffix.lower() or 'bin'}"
        )
        self.Layout()

    def _log(self, message: str) -> None:
        append_log(self.log, message)

    def _on_pick_photo(self, _event: wx.Event) -> None:
        dialog = wx.FileDialog(
            self,
            "Выберите изображение",
            wildcard="Images (*.webp;*.png;*.jpg)|*.webp;*.png;*.jpg;*.jpeg",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dialog.ShowModal() != wx.ID_OK:
            return
        self.photo_path = Path(dialog.GetPath())
        self._refresh_preview()
        self._log(f"Выбрано фото: {self.photo_path}")

    def _on_save(self, _event: wx.Event) -> None:
        student = self._build_student()
        fmt = self._current_fmt()
        suffix = ".pkl" if fmt == "pickle" else ".json"
        path = ARTIFACTS_DIR / f"student{suffix}"
        path.write_bytes(dumps_pickle(student) if fmt == "pickle" else dumps_json(student))
        photo_note = "без фото"
        if student.photo:
            photo_note = f"фото {student.photo.filename}, {len(student.photo.data)} байт"
        self._log(f"Сохранено {path.name} ({fmt}, {path.stat().st_size} байт, {photo_note})")
        self._log("Другое приложение:  python -m lab1.reader artifacts/" + path.name)

    def _on_load(self, _event: wx.Event) -> None:
        dialog = wx.FileDialog(
            self,
            "Открыть pickle или JSON",
            defaultDir=str(ARTIFACTS_DIR),
            wildcard="Student (*.pkl;*.json)|*.pkl;*.pickle;*.json",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dialog.ShowModal() != wx.ID_OK:
            return
        path = Path(dialog.GetPath())
        data = path.read_bytes()
        if path.suffix.lower() == ".json":
            student = loads_json_student(data)
        else:
            obj = loads_pickle(data)
            if not isinstance(obj, Student):
                wx.MessageBox("Файл не содержит объект Student", "Ошибка", wx.ICON_ERROR)
                return
            student = obj
        self._apply_student(student)
        self._log(f"Загружено из {path.name}: {student.greet()}")

    def _on_start_server(self, _event: wx.Event) -> None:
        if self.server and self.server.running:
            self._log("Сервер уже запущен")
            return

        def on_student(student: Student, fmt: str) -> None:
            wx.CallAfter(self._on_received, student, fmt)

        self.server = StudentServer(LAB1_HOST, LAB1_PORT, on_student=on_student)
        self.server.start()
        self._log(f"Сервер слушает {LAB1_HOST}:{LAB1_PORT}")

    def _on_received(self, student: Student, fmt: str) -> None:
        self._apply_student(student)
        extra = ""
        if student.photo:
            extra = f", фото {len(student.photo.data)} байт ({student.photo.mime})"
        self._log(f"Сервер принял ({fmt}): {student.greet()}{extra}")

    def _on_stop_server(self, _event: wx.Event) -> None:
        if self.server:
            self.server.stop()
            self._log("Сервер остановлен")

    def _on_send(self, _event: wx.Event) -> None:
        student = self._build_student()
        fmt = self._current_fmt()
        try:
            echoed = send_student(student, fmt=fmt)
        except OSError as exc:
            wx.MessageBox(
                f"Не удалось отправить: {exc}\nСначала запустите сервер (можно в этом же окне).",
                "Сеть",
                wx.ICON_WARNING,
            )
            return
        self._log(f"Клиент отправил ({fmt}) и получил эхо: {echoed.greet()}")
        if echoed.photo:
            self._log(f"Эхо-фото: {echoed.photo.filename}, {len(echoed.photo.data)} байт")

    def _form_path(self) -> Path:
        fmt = self._current_fmt()
        return ARTIFACTS_DIR / ("gui_form.pkl" if fmt == "pickle" else "gui_form.json")

    def _on_serialize_form(self, _event: wx.Event) -> None:
        state = GuiFormState(
            title="Форма студента",
            button_label="Отметиться",
            text_value=self.name_ctrl.GetValue(),
            label_text="Сериализуемая визуальная форма (кнопка + текстовое поле)",
        )
        path = self._form_path()
        if self._current_fmt() == "pickle":
            path.write_bytes(dumps_pickle(state))
        else:
            path.write_bytes(dumps_json(state))
        self._log(f"Состояние GUI сохранено в {path.name}")
        VisualFormFrame(self, state).Show()

    def _on_restore_form(self, _event: wx.Event) -> None:
        path = self._form_path()
        if not path.exists():
            wx.MessageBox("Сначала сериализуйте форму", "Нет файла", wx.ICON_INFORMATION)
            return
        data = path.read_bytes()
        if path.suffix == ".json":
            state = loads_json_form(data)
        else:
            obj = loads_pickle(data)
            state = obj if isinstance(obj, GuiFormState) else GuiFormState.from_dict(obj.to_dict())
        VisualFormFrame(self, state).Show()
        self._log(f"Форма восстановлена из {path.name}: title={state.title!r}")

    def _on_close(self, event: wx.CloseEvent) -> None:
        if self.server:
            self.server.stop()
        event.Skip()
