"""Portable stand-in for HKEY_CLASSES_ROOT: the keys pywin32 writes on `--register`."""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

from configs.cfg import ARTIFACTS_DIR

REGISTRY_PATH = ARTIFACTS_DIR / "registry.json"


def _load(path: Path = REGISTRY_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(keys: dict[str, str], path: Path = REGISTRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(keys, indent=2, ensure_ascii=False), encoding="utf-8")


def class_keys(cls: type) -> dict[str, str]:
    progid, clsid = cls._reg_progid_, cls._reg_clsid_
    command = shlex.join([sys.executable, "-m", "lab2.localserver", clsid])
    return {
        rf"HKCR\{progid}": cls._reg_desc_,
        rf"HKCR\{progid}\CLSID": clsid,
        rf"HKCR\CLSID\{clsid}": cls._reg_desc_,
        rf"HKCR\CLSID\{clsid}\ProgID": progid,
        rf"HKCR\CLSID\{clsid}\LocalServer32": command,
        rf"HKCR\CLSID\{clsid}\PythonCOM": f"{cls.__module__}.{cls.__name__}",
    }


def register(cls: type) -> dict[str, str]:
    keys = _load()
    added = class_keys(cls)
    keys.update(added)
    _save(keys)
    return added


def unregister(cls: type) -> int:
    keys = _load()
    doomed = [key for key in class_keys(cls) if key in keys]
    for key in doomed:
        del keys[key]
    _save(keys)
    return len(doomed)


def entries() -> dict[str, str]:
    return _load()


def query(key: str) -> str | None:
    return _load().get(key)
