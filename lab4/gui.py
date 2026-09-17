"""Reflection workbench: member tree, invoke by name, Java bridge."""

from __future__ import annotations

import ast
import subprocess

import wx

from configs.cfg import LAB4_HOST, LAB4_PORT, PROJECT_ROOT
from lab4.bridge_server import MethodBridge, send_request
from lab4.dynamic_student import Student, make_student
from lab4.inspector import describe
from lab4.runtime_methods import add_method_to_object, introduce, run_annotated_tests
from ui.theme import PAGE_BG, append_log, apply_window_icon, make_header, make_log, styled_button

JAVA_SRC = PROJECT_ROOT / "lab4" / "java" / "MethodSender.java"


class Lab4Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="ЛР4 · Рефлексия", size=(980, 720))
        apply_window_icon(self)
        self.student = make_student()
        self.bridge: MethodBridge | None = None

        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "ЛР4  type(), inspect, runtime methods, Java→Python"), 0, wx.EXPAND)

        body = wx.BoxSizer(wx.HORIZONTAL)
        body.Add(self._build_tree(root), 1, wx.EXPAND | wx.ALL, 10)
        body.Add(self._build_actions(root), 1, wx.EXPAND | wx.ALL, 10)
        layout.Add(body, 1, wx.EXPAND)

        self.log = make_log(root, height=220)
        layout.Add(self.log, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        root.SetSizer(layout)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self._refresh_tree()
        append_log(self.log, f"Класс создан через type(): {Student}")
        append_log(self.log, "Класс собран вызовом type('Student', (object,), namespace)")

    def _build_tree(self, parent: wx.Window) -> wx.Panel:
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(panel, label="Члены объекта Student"), 0, wx.ALL, 8)
        self.tree = wx.TreeCtrl(panel, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 8)
        panel.SetSizer(sizer)
        return panel

    def _build_actions(self, parent: wx.Window) -> wx.Panel:
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.method = wx.TextCtrl(panel, value="greet")
        self.args = wx.TextCtrl(panel, value="")
        grid = wx.FlexGridSizer(0, 2, 8, 8)
        grid.AddGrowableCol(1, 1)
        grid.Add(wx.StaticText(panel, label="Метод"), 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.method, 1, wx.EXPAND)
        grid.Add(wx.StaticText(panel, label="Аргументы"), 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.args, 1, wx.EXPAND)
        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 10)

        for label, handler in (
            ("Вызвать через getattr", self._on_invoke),
            ("Добавить introduce() в runtime", self._on_add_method),
            ("Прогнать аннотированные тесты", self._on_tests),
            ("Запустить Java-мост", self._on_start_bridge),
            ("Отправить запрос с Python", self._on_bridge_call),
            ("Java MethodSender", self._on_java),
        ):
            btn = styled_button(panel, label, primary="Вызвать" in label)
            btn.Bind(wx.EVT_BUTTON, handler)
            sizer.Add(btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        panel.SetSizer(sizer)
        return panel

    def _refresh_tree(self) -> None:
        self.tree.DeleteAllItems()
        root = self.tree.AddRoot("Student")
        for member in describe(self.student):
            label = f"{member.kind}: {member.name}{member.signature or ''} {member.value}"
            self.tree.AppendItem(root, label.strip())

    def _on_invoke(self, _event: wx.Event) -> None:
        name = self.method.GetValue().strip()
        raw = self.args.GetValue().strip()
        args = ast.literal_eval(f"({raw},)") if raw else ()
        if isinstance(args, tuple) and len(args) == 1 and raw.endswith(","):
            pass
        try:
            result = getattr(self.student, name)(*args)
        except Exception as exc:
            append_log(self.log, f"getattr ошибка: {exc}")
            return
        append_log(self.log, f"getattr({name!r}){args} -> {result!r}")

    def _on_add_method(self, _event: wx.Event) -> None:
        add_method_to_object(self.student, "introduce", introduce)
        self._refresh_tree()
        append_log(self.log, "Добавлен introduce(suffix) через types.MethodType")
        append_log(self.log, self.student.introduce("runtime"))

    def _on_tests(self, _event: wx.Event) -> None:
        for line in run_annotated_tests():
            append_log(self.log, line)

    def _on_start_bridge(self, _event: wx.Event) -> None:
        if self.bridge and self.bridge.running:
            append_log(self.log, "Мост уже запущен")
            return
        self.bridge = MethodBridge()
        self.bridge.target = self.student
        add_method_to_object(self.student, "introduce", introduce)
        self.bridge.start()
        append_log(self.log, f"Java→Python мост на {LAB4_HOST}:{LAB4_PORT}")

    def _on_bridge_call(self, _event: wx.Event) -> None:
        name = self.method.GetValue().strip()
        raw = self.args.GetValue().strip()
        args = list(ast.literal_eval(f"[{raw}]") if raw else [])
        try:
            reply = send_request(name, args)
        except OSError as exc:
            append_log(self.log, f"Мост недоступен: {exc}")
            return
        append_log(self.log, f"bridge {reply}")

    def _on_java(self, _event: wx.Event) -> None:
        if subprocess.run(["which", "javac"], capture_output=True).returncode != 0:
            append_log(self.log, "javac не найден. Исходник: lab4/java/MethodSender.java")
            return
        work = JAVA_SRC.parent
        compiled = subprocess.run(["javac", str(JAVA_SRC)], cwd=work, capture_output=True, text=True)
        if compiled.returncode != 0:
            append_log(self.log, compiled.stderr)
            return
        ran = subprocess.run(
            ["java", "-cp", str(work), "MethodSender", LAB4_HOST, str(LAB4_PORT), "greet"],
            capture_output=True,
            text=True,
        )
        append_log(self.log, (ran.stdout or ran.stderr).strip())

    def _on_close(self, event: wx.CloseEvent) -> None:
        if self.bridge:
            self.bridge.stop()
        event.Skip()
