"""Domain objects for serialization labs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Photo:
    filename: str
    mime: str
    data: bytes

    def __repr__(self) -> str:
        return f"Photo(filename={self.filename!r}, mime={self.mime!r}, bytes={len(self.data)})"


@dataclass
class Student:
    name: str
    group: str
    faculty: str
    photo: Photo | None = None

    def greet(self) -> str:
        return f"{self.name}, {self.group}, {self.faculty}"


@dataclass
class GuiFormState:
    """Serializable snapshot of a tiny visual form (button + text field)."""

    title: str = "Визуальная форма"
    button_label: str = "Нажми меня"
    text_value: str = ""
    label_text: str = "Добро пожаловать"
    extra: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "button_label": self.button_label,
            "text_value": self.text_value,
            "label_text": self.label_text,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GuiFormState:
        return cls(
            title=str(data.get("title", "Визуальная форма")),
            button_label=str(data.get("button_label", "Нажми меня")),
            text_value=str(data.get("text_value", "")),
            label_text=str(data.get("label_text", "")),
            extra=dict(data.get("extra") or {}),
        )
