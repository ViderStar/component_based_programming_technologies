"""COM class: basic algebra, declared the pywin32 way (`_reg_*_`, `_public_methods_`)."""

from __future__ import annotations

import math

CLSCTX_LOCAL_SERVER = 4  # pythoncom.CLSCTX_LOCAL_SERVER, without importing pywin32


def _tidy(value: float) -> float | int:
    if not math.isfinite(value):
        raise OverflowError("result is out of range")
    return int(value) if value.is_integer() and abs(value) < 1e15 else value


class Calculator:
    _reg_progid_ = "Lab2.Calculator"
    _reg_clsid_ = "{7C1B9A52-3E64-4F0A-9D21-5B8E0C6A2F14}"
    _reg_desc_ = "Lab 2 calculator COM server"
    _reg_clsctx_ = CLSCTX_LOCAL_SERVER
    _public_methods_ = ["Add", "Sub", "Mul", "Div", "Pow"]

    def Add(self, a: float, b: float) -> float | int:
        return _tidy(float(a) + float(b))

    def Sub(self, a: float, b: float) -> float | int:
        return _tidy(float(a) - float(b))

    def Mul(self, a: float, b: float) -> float | int:
        return _tidy(float(a) * float(b))

    def Div(self, a: float, b: float) -> float | int:
        if float(b) == 0:
            raise ZeroDivisionError("division by zero")
        return _tidy(float(a) / float(b))

    def Pow(self, a: float, b: float) -> float | int:
        return _tidy(math.pow(float(a), float(b)))

    def secret(self) -> str:
        """Not in `_public_methods_`, so COM clients cannot reach it."""
        return "hidden"
