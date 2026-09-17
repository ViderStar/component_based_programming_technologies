"""TCP client that sends a framed Student payload and reads the echo."""

from __future__ import annotations

import socket

from configs.cfg import LAB1_HOST, LAB1_PORT
from lab1.codecs import dumps_json, dumps_pickle, loads_json_student, loads_pickle
from lab1.models import Student
from lab1.net import pack_envelope, recv_message, send_message, unpack_envelope


def send_student(
    student: Student,
    fmt: str = "pickle",
    host: str = LAB1_HOST,
    port: int = LAB1_PORT,
    timeout: float = 5.0,
) -> Student:
    payload = dumps_pickle(student) if fmt == "pickle" else dumps_json(student)
    with socket.create_connection((host, port), timeout=timeout) as sock:
        send_message(sock, pack_envelope(fmt, payload))
        fmt_back, echoed = unpack_envelope(recv_message(sock))
    if fmt_back == "pickle":
        obj = loads_pickle(echoed)
        if not isinstance(obj, Student):
            raise TypeError("echo is not a Student")
        return obj
    return loads_json_student(echoed)
