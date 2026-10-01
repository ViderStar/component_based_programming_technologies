"""Real COM registration with pywin32 (Windows only).

    pip install pywin32
    python lab2\\windows\\calc_com_server.py --register      (administrator prompt)
    python lab2\\windows\\calc_com_server.py --unregister

Wraps the same `lab2.calculator.Calculator` that the portable GUI uses.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pythoncom
import win32com.server.register

from lab2.calculator import Calculator as PortableCalculator


class Calculator(PortableCalculator):
    _reg_clsctx_ = pythoncom.CLSCTX_LOCAL_SERVER


if __name__ == "__main__":
    print("Registering COM server with CLSID:", Calculator._reg_clsid_)
    win32com.server.register.UseCommandLine(Calculator)
