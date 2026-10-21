"""Real window screenshots for the reports (macOS): `screencapture -l <window id>` per frame."""

from __future__ import annotations

import ctypes
import subprocess
import sys
from pathlib import Path

import wx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SHOTS = ROOT / "reports" / "screenshots"


def window_number(frame: wx.Frame) -> int:
    objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
    objc.sel_registerName.restype = ctypes.c_void_p
    objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    objc.objc_msgSend.restype = ctypes.c_void_p
    window = objc.objc_msgSend(frame.GetHandle(), objc.sel_registerName(b"window"))
    objc.objc_msgSend.restype = ctypes.c_long
    return objc.objc_msgSend(window, objc.sel_registerName(b"windowNumber"))


def settle(ms: int = 600) -> None:
    for _ in range(ms // 50):
        wx.Yield()
        wx.MilliSleep(50)


def shoot(frame: wx.Frame, name: str) -> None:
    settle()
    target = SHOTS / name
    subprocess.run(["screencapture", "-x", "-o", "-l", str(window_number(frame)), str(target)], check=True)
    print(f"capture {name} ({target.stat().st_size} bytes)")


def shoot_launcher() -> None:
    from ui.launcher import LauncherFrame

    launcher = LauncherFrame()
    launcher.Show()
    shoot(launcher, "launcher.png")
    launcher.Destroy()


def shoot_labs_1_2() -> None:
    import lab2.gui as lab2_gui
    from lab1.extras.reflection.gui import ReflectionFrame
    from lab1.extras.rpc.gui import RpcFrame
    from lab1.gui import Lab1Frame
    from lab2 import cases as lab2_cases
    from lab2.web import WebServer

    lab1 = Lab1Frame()
    lab1.Show()
    for index in range(5):  # the sixth case opens a second window
        lab1.cases.run_index(index)
    shoot(lab1, "lab1.png")
    lab1.Close()

    lab2_gui.open_excel = lambda path: "Microsoft Excel"  # do not launch Excel while shooting
    lab2_cases._WEB = WebServer(port=18022)  # the default port may be taken by a running window
    lab2_cases._WEB.start()
    lab2 = lab2_gui.Lab2Frame()
    lab2.Show()
    for index in range(len(lab2.cases._cases)):
        lab2.cases.run_index(index)
    lab2.book.ChangeSelection(0)
    shoot(lab2, "lab2.png")
    lab2.keypad.clear()
    for key in ("1", "÷", "0", "="):
        lab2.keypad.press(key)
    shoot(lab2, "lab2_error.png")
    lab2.book.ChangeSelection(1)
    shoot(lab2, "lab2_com.png")
    lab2.book.ChangeSelection(2)
    lab2._load_page()
    settle(1500)
    if lab2.browser is not None:
        lab2.browser.RunScript("calculate()")
    shoot(lab2, "lab2_html.png")
    lab2.Close()

    for factory, name in ((RpcFrame, "lab1_extra_rpc.png"), (ReflectionFrame, "lab1_extra_reflection.png")):
        frame = factory()
        frame.Show()
        for index in range(len(frame.cases._cases) if hasattr(frame, "cases") else 0):
            frame.cases.run_index(index)
        shoot(frame, name)
        frame.Close()
    settle(200)




def shoot_lab3() -> None:
    """The Brython window: one shot per tab of the site, all cases passed."""
    from lab3 import cases
    from lab3.gui import Lab3Frame

    frame = Lab3Frame()
    frame.Show()
    settle(2500)  # Brython compiles the page in the web view
    for index in range(len(frame.cases._cases)):
        frame.cases.run_index(index)
    shoot(frame, "lab3.png")
    for name, page, query in (
        ("lab3_regression.png", "index.html", "?tab=regression"),
        ("lab3_optimum.png", "index.html", "?tab=optimum"),
        ("lab3_examples.png", "examples.html", ""),
    ):
        frame.open_page(page, query)
        settle(2500)
        shoot(frame, name)
    frame.Close()
    cases.stop_server()


def shoot_lab4() -> None:
    """The Jython window, plus the Swing content rendered by the lab itself (no screen needed)."""
    from lab4 import runtime
    from lab4.gui import Lab4Frame

    frame = Lab4Frame()
    frame.Show()
    for index in range(len(frame.cases._cases)):
        frame.cases.run_index(index)
    frame.preview("sine")
    shoot(frame, "lab4.png")
    frame.Close()
    for name, view, popup in (
        ("lab4_picture1.png", "picture1", None),
        ("lab4_picture2.png", "picture2", None),
        ("lab4_sine.png", "sine", None),
        ("lab4_menu.png", "sine", "Draw"),
    ):
        args = ["--snapshot", str(SHOTS / name), "--view", view, "--frame"] + (["--popup", popup] if popup else [])
        runtime.run_jython("menu_app.py", *args)
        print(f"render {name}")


def main() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    app = wx.App(False)
    wanted = set(sys.argv[1:]) or {"launcher", "lab1", "lab2"}
    if "launcher" in wanted:
        shoot_launcher()
    if wanted & {"lab1", "lab2"}:
        shoot_labs_1_2()
    if "lab3" in wanted:
        shoot_lab3()
    if "lab4" in wanted:
        shoot_lab4()


if __name__ == "__main__":
    main()
    sys.exit(0)
