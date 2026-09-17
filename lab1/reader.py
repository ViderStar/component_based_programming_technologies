"""Separate application: deserialize a Student dumped by the main GUI/CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lab1.codecs import loads_json_student, loads_pickle
from lab1.models import Student


def load_student(path: Path) -> Student:
    data = path.read_bytes()
    if path.suffix.lower() in {".json", ".jsn"}:
        return loads_json_student(data)
    if path.suffix.lower() in {".pkl", ".pickle"}:
        obj = loads_pickle(data)
        if not isinstance(obj, Student):
            raise TypeError(f"{path} does not contain a Student")
        return obj
    try:
        return loads_json_student(data)
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError):
        obj = loads_pickle(data)
        if not isinstance(obj, Student):
            raise TypeError(f"{path} does not contain a Student") from None
        return obj


def main() -> None:
    parser = argparse.ArgumentParser(description="Deserialize a Student from pickle/JSON.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    student = load_student(args.path)
    photo = "none"
    if student.photo is not None:
        photo = f"{student.photo.filename} ({student.photo.mime}, {len(student.photo.data)} bytes)"
    print(f"name     : {student.name}")
    print(f"group    : {student.group}")
    print(f"faculty  : {student.faculty}")
    print(f"photo    : {photo}")
    print(f"greet()  : {student.greet()}")


if __name__ == "__main__":
    main()
