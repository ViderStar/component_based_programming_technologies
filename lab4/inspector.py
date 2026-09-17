"""Runtime inspection of objects and classes."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any


@dataclass
class Member:
    name: str
    kind: str
    signature: str
    value: str


def describe(target: Any) -> list[Member]:
    members: list[Member] = []
    for name, value in inspect.getmembers(target):
        if name.startswith("_"):
            continue
        if inspect.ismethod(value) or inspect.isfunction(value):
            try:
                signature = str(inspect.signature(value))
            except (TypeError, ValueError):
                signature = "(?)"
            members.append(Member(name, "method", signature, getattr(value, "__qualname__", name)))
            continue
        if inspect.isdatadescriptor(value):
            members.append(Member(name, "descriptor", "", type(value).__name__))
            continue
        members.append(Member(name, "field", "", repr(value)))
    return members


def format_report(target: Any) -> str:
    lines = [f"type = {type(target)!r}", f"class created dynamically: {type(target).__module__}"]
    for member in describe(target):
        if member.kind == "method":
            lines.append(f"  method {member.name}{member.signature}")
        else:
            lines.append(f"  {member.kind:10} {member.name} = {member.value}")
    return "\n".join(lines)
