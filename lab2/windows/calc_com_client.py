"""pywin32 client for the registered calculator (Windows only)."""

import win32com.client

calc = win32com.client.Dispatch("Lab2.Calculator")
print("2 + 3 =", calc.Add(2, 3))
print("7 - 10 =", calc.Sub(7, 10))
print("6 * 7 =", calc.Mul(6, 7))
print("7 / 2 =", calc.Div(7, 2))
print("2 ^ 10 =", calc.Pow(2, 10))
