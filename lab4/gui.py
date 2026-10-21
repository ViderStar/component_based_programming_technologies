"""Lab 4 window: previews of the Jython menu application and the checklist of cases.

The Swing windows themselves are separate Jython processes started by the buttons.
"""

from __future__ import annotations

import wx

from lab4 import cases, runtime
from lab4.runtime import WORK_DIR
from ui.cases import CasePanel
from ui.theme import MUTED, PAGE_BG, append_log, apply_window_icon, make_header, make_log, styled_button

VIEWS = [("Picture 1", "picture1"), ("Picture 2", "picture2"), ("Sine wave", "sine")]
PREVIEW = WORK_DIR / "preview.png"


class Lab4Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="Lab 4", size=(1180, 720))
        apply_window_icon(self)
        self._children: list = []
        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "Lab 4  Jython"), 0, wx.EXPAND)

        body = wx.BoxSizer(wx.HORIZONTAL)
        left = wx.BoxSizer(wx.VERTICAL)
        self.environment = wx.StaticText(root, label=self._environment())
        self.environment.SetForegroundColour(MUTED)
        left.Add(self.environment, 0, wx.BOTTOM, 6)

        row = wx.BoxSizer(wx.HORIZONTAL)
        for title, view in VIEWS:
            button = styled_button(root, title, primary=False)
            button.Bind(wx.EVT_BUTTON, lambda _e, v=view: self.preview(v))
            row.Add(button, 0, wx.RIGHT, 6)
        row.AddStretchSpacer()
        for title, script, args in (
            ("Menu application", "menu_app.py", ()),
            ("Greet frame", "greet_frame.py", ()),
            ("Image viewer", "image_viewer.py", (str(cases.PICTURES["picture1"]),)),
        ):
            button = styled_button(root, title)
            button.Bind(wx.EVT_BUTTON, lambda _e, s=script, a=args: self.launch(s, *a))
            row.Add(button, 0, wx.LEFT, 6)
        left.Add(row, 0, wx.EXPAND | wx.BOTTOM, 8)

        self.bitmap = wx.StaticBitmap(root, bitmap=wx.Bitmap(640, 444))
        self.bitmap.SetBackgroundColour(wx.WHITE)
        left.Add(self.bitmap, 1, wx.EXPAND)
        self.log = make_log(root, height=90)
        left.Add(self.log, 0, wx.EXPAND | wx.TOP, 8)
        body.Add(left, 1, wx.EXPAND | wx.ALL, 8)

        self.cases = CasePanel(
            root,
            [
                ("Java + Jython", cases.environment),
                ("hello world", cases.hello_world),
                ("files (java.io)", cases.files),
                ("class extends Object", cases.python_class_extends_java),
                ("ArrayList", cases.java_collections),
                ("jar import", cases.jar_import),
                ("Java calls Python", cases.java_calls_python),
                ("images and sound", cases.images_and_sound),
                ("menu items", cases.menu_items),
                ("menu: picture 1", cases.menu_picture1),
                ("menu: picture 2", cases.menu_picture2),
                ("menu: sine wave", cases.menu_sine),
                ("menu: whole window", cases.menu_window),
                ("JFrame on screen", cases.swing_window),
            ],
        )
        body.Add(self.cases, 0, wx.EXPAND | wx.ALL, 8)
        layout.Add(body, 1, wx.EXPAND)
        root.SetSizer(layout)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Centre()
        if runtime.available():
            self.preview("sine")

    @staticmethod
    def _environment() -> str:
        try:
            java, jar = runtime.require()
        except runtime.JythonUnavailable as exc:
            return str(exc)
        return f"{java}  ·  {jar.name}"

    def preview(self, view: str) -> None:
        """Render the window content (menu bar, canvas, status line) headlessly and show the PNG."""
        try:
            WORK_DIR.mkdir(parents=True, exist_ok=True)
            runtime.run_jython("menu_app.py", "--snapshot", str(PREVIEW), "--view", view, "--frame", "--popup", "Draw")
        except Exception as exc:
            append_log(self.log, f"preview failed: {exc}")
            return
        image = wx.Image(str(PREVIEW))
        self.bitmap.SetBitmap(wx.Bitmap(image))
        self.bitmap.GetParent().Layout()
        append_log(self.log, f"preview: menu_app.py --view {view} --frame --popup Draw")

    def launch(self, script: str, *args: str) -> None:
        try:
            self._children.append(runtime.launch_jython(script, *args))
        except runtime.JythonUnavailable as exc:
            append_log(self.log, str(exc))
            return
        append_log(self.log, f"started {script} in a separate JVM")

    def _on_close(self, event: wx.CloseEvent) -> None:
        for child in self._children:
            if child.poll() is None:
                child.terminate()
        event.Skip()
