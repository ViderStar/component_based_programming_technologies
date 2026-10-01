"""Entry point: GUI launcher or CLI lab runners."""

from __future__ import annotations

import argparse
import logging

from lab1.extras.reflection.runner import run_reflection
from lab1.extras.rpc.runner import run_rpc
from lab1.extras.wxui.runner import run_wxui
from lab1.runner import run_lab1
from lab2.runner import run_lab2

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
    from lab1.gui import Lab1Frame

    return Lab1Frame


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Component-based programming labs."
    )
    parser.add_argument("--gui", action="store_true", help="Open the wxPython window instead of the CLI run.")
    parser.add_argument(
        "--lab",
        choices=("1", "2"),
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
        help="Run CLI demos for both labs and the Lab 1 extras.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.all:
        run_lab1()
        for run_extra in EXTRAS.values():
            run_extra()
        run_lab2()
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
    else:
        run_lab1()


if __name__ == "__main__":
    main()
