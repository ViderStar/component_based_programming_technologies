"""Entry point: GUI launcher or CLI lab runners."""

from __future__ import annotations

import argparse
import logging

from lab1.runner import run_lab1
from lab2.runner import run_lab2
from lab3.runner import run_lab3
from lab4.runner import run_lab4


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Component-based programming labs."
    )
    parser.add_argument("--gui", action="store_true", help="Open the wxPython launcher.")
    parser.add_argument(
        "--lab",
        choices=("1", "2", "3", "4"),
        help="Lab number for the CLI run.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run CLI demos for all four labs.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.all:
        run_lab1()
        run_lab2()
        run_lab3()
        run_lab4()
        return

    if args.lab == "1":
        if args.gui:
            from lab1.gui import Lab1Frame
            import wx

            app = wx.App(False)
            Lab1Frame().Show()
            app.MainLoop()
            return
        run_lab1()
        return
    if args.lab == "2":
        if args.gui:
            from lab2.gui import Lab2Frame
            import wx

            app = wx.App(False)
            Lab2Frame().Show()
            app.MainLoop()
            return
        run_lab2()
        return
    if args.lab == "3":
        from lab3.app import Lab3Frame
        import wx

        app = wx.App(False)
        Lab3Frame().Show()
        app.MainLoop()
        return
    if args.lab == "4":
        if args.gui:
            from lab4.gui import Lab4Frame
            import wx

            app = wx.App(False)
            Lab4Frame().Show()
            app.MainLoop()
            return
        run_lab4()
        return

    from ui.launcher import run_launcher

    run_launcher()


if __name__ == "__main__":
    main()
