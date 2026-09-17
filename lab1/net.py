"""Length-prefixed TCP framing. Avoids the 1024-byte recv() trap from the handout."""

from __future__ import annotations

import socket
import struct

MAX_PAYLOAD = 16 * 1024 * 1024
HEADER = struct.Struct("!I")


def send_message(sock: socket.socket, payload: bytes) -> None:
    if len(payload) > MAX_PAYLOAD:
        raise ValueError(f"payload too large: {len(payload)} bytes")
    sock.sendall(HEADER.pack(len(payload)) + payload)


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        piece = sock.recv(size - len(chunks))
        if not piece:
            raise ConnectionError("socket closed while reading")
        chunks.extend(piece)
    return bytes(chunks)


def recv_message(sock: socket.socket) -> bytes:
    (length,) = HEADER.unpack(recv_exact(sock, HEADER.size))
    if length > MAX_PAYLOAD:
        raise ValueError(f"declared payload too large: {length}")
    return recv_exact(sock, length)


def pack_envelope(fmt: str, payload: bytes) -> bytes:
    token = fmt.encode("ascii")[:8].ljust(8, b"\0")
    return token + payload


def unpack_envelope(blob: bytes) -> tuple[str, bytes]:
    if len(blob) < 8:
        raise ValueError("envelope too short")
    fmt = blob[:8].rstrip(b"\0").decode("ascii")
    return fmt, blob[8:]
