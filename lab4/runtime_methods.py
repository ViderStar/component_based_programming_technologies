"""Add methods at runtime and annotation-style expected-output tests."""

from __future__ import annotations

import types
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def expected(input_value: Any, output_value: Any) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        fn._expected = (input_value, output_value)  # type: ignore[attr-defined]
        return fn

    return decorator


class Probe:
    """Stationary class with two annotated methods (old Java reflection lab)."""

    @expected(1, "Hie, Dear")
    def get_str(self, index: int) -> str:
        mapping = {1: "Hie, Dear", 2: "Bye-Bye"}
        return mapping.get(index, "What happens?")

    @expected("ITAS", "faculty=ITAS")
    def tag(self, faculty: str) -> str:
        return f"faculty={faculty}"


def run_annotated_tests(instance: Any | None = None) -> list[str]:
    target = instance or Probe()
    lines: list[str] = []
    for name, method in inspect_expected_methods(target):
        argument, want = method._expected
        got = method(argument)
        status = "PASS" if got == want else "FAIL"
        lines.append(f"{status} {name}({argument!r}) -> {got!r} (expected {want!r})")
    return lines


def inspect_expected_methods(instance: Any) -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    for name in dir(instance):
        if name.startswith("_"):
            continue
        attr = getattr(instance, name)
        if callable(attr) and hasattr(attr, "_expected"):
            found.append((name, attr))
    return found


def add_method_to_object(obj: Any, name: str, func: Callable[..., Any]) -> None:
    setattr(obj, name, types.MethodType(func, obj))


def add_method_to_class(cls: type, name: str, func: Callable[..., Any]) -> None:
    setattr(cls, name, func)


def introduce(self, suffix: str = "ИТАС") -> str:
    return f"{self.name} / {self.group} / {suffix}"
