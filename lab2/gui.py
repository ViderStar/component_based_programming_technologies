"""XML-RPC client workbench."""

from __future__ import annotations

import ast
import json
import subprocess

import wx

from configs.cfg import LAB2_HOST, LAB2_PORT, PROJECT_ROOT
from lab2.rpc_client import call, make_proxy
from lab2.rpc_server import RpcServer
from ui.theme import PAGE_BG, append_log, apply_window_icon, make_header, make_log, styled_button

JAVA_SRC = PROJECT_ROOT / "lab2" / "java" / "XmlRpcClient.java"


class Lab2Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="ЛР2 · Удалённый вызов модулей (XML-RPC)", size=(900, 680))
        apply_window_icon(self)
        self.server: RpcServer | None = None

        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "ЛР2  XML-RPC: вызов модуля по имени"), 0, wx.EXPAND)

        card = wx.Panel(root)
        card.SetBackgroundColour(wx.WHITE)
        form = wx.FlexGridSizer(0, 2, 8, 8)
        form.AddGrowableCol(1, 1)

        self.method = wx.ComboBox(
            card,
            choices=["add", "mul", "greet_student", "inspect_module", "system.listMethods"],
            style=wx.CB_DROPDOWN,
        )
        self.method.SetValue("add")
        self.args = wx.TextCtrl(card, value="5, 3")
        form.Add(wx.StaticText(card, label="Метод"), 0, wx.ALIGN_CENTER_VERTICAL)
        form.Add(self.method, 1, wx.EXPAND)
        form.Add(wx.StaticText(card, label="Аргументы (Python-литералы)"), 0, wx.ALIGN_CENTER_VERTICAL)
        form.Add(self.args, 1, wx.EXPAND)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        for label, handler in (
            ("Запустить сервер", self._on_start),
            ("Остановить", self._on_stop),
            ("Вызвать", self._on_call),
            ("Java-клиент", self._on_java),
        ):
            btn = styled_button(card, label, primary=label == "Вызвать")
            btn.Bind(wx.EVT_BUTTON, handler)
            buttons.Add(btn, 0, wx.RIGHT, 8)

        card_sizer = wx.BoxSizer(wx.VERTICAL)
        card_sizer.Add(form, 0, wx.EXPAND | wx.ALL, 12)
        card_sizer.Add(buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        hint = wx.StaticText(
            card,
            label="Сервер: xmlrpc.server.SimpleXMLRPCServer. Клиент Python — xmlrpc.client. "
            "Java шлёт тот же XML methodCall по HTTP POST. CGI из лекции в код не входит: cgi удалён в Python 3.13+.",
        )
        hint.Wrap(820)
        card_sizer.Add(hint, 0, wx.ALL, 12)
        card.SetSizer(card_sizer)

        layout.Add(card, 0, wx.EXPAND | wx.ALL, 12)
        self.log = make_log(root, height=320)
        layout.Add(self.log, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        root.SetSizer(layout)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        append_log(self.log, f"Цель сервера: http://{LAB2_HOST}:{LAB2_PORT}/")

    def _on_start(self, _event: wx.Event) -> None:
        if self.server and self.server.running:
            append_log(self.log, "Сервер уже работает")
            return
        self.server = RpcServer()
        self.server.start()
        append_log(self.log, f"XML-RPC сервер запущен на {LAB2_HOST}:{LAB2_PORT}")

    def _on_stop(self, _event: wx.Event) -> None:
        if self.server:
            self.server.stop()
            append_log(self.log, "Сервер остановлен")

    def _parse_args(self) -> tuple:
        raw = self.args.GetValue().strip()
        if not raw:
            return ()
        value = ast.literal_eval(f"({raw},)" if "," not in raw else f"({raw})")
        if not isinstance(value, tuple):
            return (value,)
        if len(value) == 1 and isinstance(value[0], tuple):
            return value[0]
        return value

    def _on_call(self, _event: wx.Event) -> None:
        method = self.method.GetValue().strip()
        try:
            args = self._parse_args()
            if method == "system.listMethods":
                result = make_proxy().system.listMethods()
            else:
                result = call(method, *args)
        except Exception as exc:
            append_log(self.log, f"Ошибка: {exc}")
            return
        pretty = json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, (dict, list)) else repr(result)
        append_log(self.log, f"{method}{args} -> {pretty}")

    def _on_java(self, _event: wx.Event) -> None:
        javac = subprocess.run(["which", "javac"], capture_output=True, text=True)
        if javac.returncode != 0:
            append_log(self.log, "javac не найден. Пример исходника: lab2/java/XmlRpcClient.java")
            return
        work = PROJECT_ROOT / "lab2" / "java"
        compile_res = subprocess.run(["javac", str(JAVA_SRC)], cwd=work, capture_output=True, text=True)
        if compile_res.returncode != 0:
            append_log(self.log, compile_res.stderr or compile_res.stdout)
            return
        args = self.args.GetValue().replace(",", " ").split()
        cmd = ["java", "-cp", str(work), "XmlRpcClient", LAB2_HOST, str(LAB2_PORT), self.method.GetValue(), *args[:2]]
        run_res = subprocess.run(cmd, capture_output=True, text=True)
        append_log(self.log, (run_res.stdout or run_res.stderr).strip() or "Java-клиент завершился без вывода")

    def _on_close(self, event: wx.CloseEvent) -> None:
        if self.server:
            self.server.stop()
        event.Skip()
