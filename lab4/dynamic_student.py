"""Dynamically constructed Student class (type())."""

from __future__ import annotations

from configs.cfg import DEFAULT_STUDENT


def _init(self, name: str | None = None, group: str | None = None) -> None:
    self.name = name or DEFAULT_STUDENT["name"]
    self.group = group or DEFAULT_STUDENT["group"]


def _greet(self) -> str:
    return f"Hello, from {self.name}"


def _repr(self) -> str:
    return f"Student(name={self.name!r}, group={self.group!r})"


Student = type(
    "Student",
    (object,),
    {
        "__init__": _init,
        "greet": _greet,
        "__repr__": _repr,
        "__module__": "lab4.dynamic_student",
        "__doc__": "Student created at runtime via type().",
    },
)


def make_student(name: str | None = None, group: str | None = None) -> Student:
    return Student(name, group)
