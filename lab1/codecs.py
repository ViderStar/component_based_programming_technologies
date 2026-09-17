"""Pickle and JSON codecs, including WebP as raw bytes or base64."""

from __future__ import annotations

import base64
import json
import pickle
from pathlib import Path
from typing import Any

from helpers.images import sniff_mime
from lab1.models import GuiFormState, Photo, Student

PICKLE_PROTOCOL = pickle.HIGHEST_PROTOCOL


def student_to_jsonable(student: Student) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": student.name,
        "group": student.group,
        "faculty": student.faculty,
        "photo": None,
    }
    if student.photo is not None:
        payload["photo"] = {
            "filename": student.photo.filename,
            "mime": student.photo.mime,
            "encoding": "base64",
            "data": base64.b64encode(student.photo.data).decode("ascii"),
        }
    return payload


def student_from_jsonable(data: dict[str, Any]) -> Student:
    photo_raw = data.get("photo")
    photo: Photo | None = None
    if isinstance(photo_raw, dict) and photo_raw.get("data"):
        raw = photo_raw["data"]
        if photo_raw.get("encoding") == "base64" or (
            isinstance(raw, str) and not isinstance(raw, bytes)
        ):
            decoded = base64.b64decode(raw)
        else:
            decoded = bytes(raw)
        photo = Photo(
            filename=str(photo_raw.get("filename", "photo.bin")),
            mime=str(photo_raw.get("mime", "application/octet-stream")),
            data=decoded,
        )
    return Student(
        name=str(data["name"]),
        group=str(data["group"]),
        faculty=str(data["faculty"]),
        photo=photo,
    )


def dumps_pickle(obj: Any) -> bytes:
    return pickle.dumps(obj, protocol=PICKLE_PROTOCOL)


def loads_pickle(payload: bytes) -> Any:
    return pickle.loads(payload)


def dumps_json(student: Student | GuiFormState | dict) -> bytes:
    if isinstance(student, Student):
        body = student_to_jsonable(student)
    elif isinstance(student, GuiFormState):
        body = student.to_dict()
    else:
        body = student
    return json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")


def loads_json_student(payload: bytes | str) -> Student:
    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    return student_from_jsonable(json.loads(text))


def loads_json_form(payload: bytes | str) -> GuiFormState:
    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    return GuiFormState.from_dict(json.loads(text))


def attach_photo(student: Student, path: str | Path) -> Student:
    file_path = Path(path)
    data = file_path.read_bytes()
    student.photo = Photo(
        filename=file_path.name,
        mime=sniff_mime(file_path, data),
        data=data,
    )
    return student


def photo_from_data_url(data_url: str, filename: str = "photo.webp") -> Photo:
    header, _, encoded = data_url.partition(",")
    mime = "image/webp"
    if header.startswith("data:") and ";base64" in header:
        mime = header[5:].split(";", 1)[0] or mime
    return Photo(filename=filename, mime=mime, data=base64.b64decode(encoded))
