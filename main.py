"""Entry point: GUI launcher or CLI lab runners."""

from __future__ import annotations

import argparse
import logging

from lab1.extras.reflection.runner import run_reflection
from lab1.extras.rpc.runner import run_rpc
from lab1.extras.wxui.runner import run_wxui
from lab1.runner import run_lab1
from lab2.runner import run_lab2
from lab3.runner import run_lab3
from lab4.runner import run_lab4
from lab5.runner import run_lab5

EXTRAS = {"rpc": run_rpc, "wxui": run_wxui, "reflection": run_reflection}


def _frame(lab: str, extra: str | None):
    if extra == "rpc":
        from lab1.extras.rpc.gui import RpcFrame

        return RpcFrame
    if extra == "wxui":
        from lab1.extras.wxui.app import WxuiFrame

        return WxuiFrame
    if extra == "reflection":
        from lab1.extras.reflection.gui import ReflectionFrame

        return ReflectionFrame
    if lab == "2":
        from lab2.gui import Lab2Frame

        return Lab2Frame
    if lab == "3":
        from lab3.gui import Lab3Frame

        return Lab3Frame
    if lab == "4":
        from lab4.gui import Lab4Frame

        return Lab4Frame
    if lab == "5":
        from lab5.gui import Lab5Frame

        return Lab5Frame
    from lab1.gui import Lab1Frame

    return Lab1Frame


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Component-based programming labs."
    )
    parser.add_argument("--gui", action="store_true", help="Open the wxPython window instead of the CLI run.")
    parser.add_argument(
        "--lab",
        choices=("1", "2", "3", "4", "5"),
        help="Lab number for the CLI run.",
    )
    parser.add_argument(
        "--extra",
        choices=tuple(EXTRAS),
        help="Lab 1 extra to run instead of the lab itself.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run CLI demos for all labs and the Lab 1 extras.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.all:
        run_lab1()
        for run_extra in EXTRAS.values():
            run_extra()
        run_lab2()
        run_lab3()
        run_lab4()
        run_lab5()
        return

    if args.lab is None and args.extra is None:
        from ui.launcher import run_launcher

        run_launcher()
        return

    if args.gui or args.extra == "wxui":
        import wx

        app = wx.App(False)
        _frame(args.lab, args.extra)().Show()
        app.MainLoop()
        return

    if args.extra is not None:
        EXTRAS[args.extra]()
    elif args.lab == "2":
        run_lab2()
    elif args.lab == "3":
        run_lab3()
    elif args.lab == "4":
        run_lab4()
    elif args.lab == "5":
        run_lab5()
    else:
        run_lab1()


if __name__ == "__main__":
    main()
