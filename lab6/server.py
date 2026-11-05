"""Streaming web server of Lab 6 on `http.server`.

| Route | Answer |
| --- | --- |
| `GET /` | the player page: ask by text, answers with `<audio>`, recordings, live picture |
| `GET /image?text=` | a PNG drawn by Pillow (the handout's `/image`) |
| `GET /stream-image?frames=` | `multipart/x-mixed-replace` JPEG frames of a clock, one per second |
| `GET /audio/<file>.wav`, `/stream/<file>.wav` | a WAV sent in 16 KiB chunks, with `Range` for the browser's player |
| `GET /recordings` | JSON list of the uploaded recordings |
| `POST /upload?name=` | save a WAV recorded by the client |
| `POST /ask` `{"text": ...}` | text → WAV (server voice) → classifier → answer text and answer WAV |
| `POST /ask-wav` | the same for a WAV without text: the recording itself is classified |
"""

from __future__ import annotations

import io
import json
import math
import re
import threading
import time
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from configs.cfg import LAB6_WEB_HOST, LAB6_WEB_PORT
from lab6 import voice
from lab6.classifier import DATA_DIR, SERVER_VOICE, IntentClassifier, available_voices

RECORDINGS_DIR = DATA_DIR / "recordings"
ANSWERS_DIR = DATA_DIR / "answers"
PAGE = Path(__file__).resolve().parent / "page.html"
CHUNK = 16 * 1024
SAFE_NAME = re.compile(r"^[\w.-]+\.wav$")

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "There are ten kinds of people: those who understand binary and those who do not.",
    "A SQL query walks into a bar, walks up to two tables and asks: can I join you?",
    "Why did the component fail the interview? It had too many dependencies.",
]

_model: IntentClassifier | None = None
_model_lock = threading.Lock()
_jokes = iter(range(10**9))


def model() -> IntentClassifier:
    """The classifier, trained on the first request (or loaded from `artifacts/lab6/model.pkl`)."""
    global _model
    with _model_lock:
        if _model is None:
            _model = IntentClassifier.load()
        return _model


# ---------------------------------------------------------------- answers


def melody(path: Path) -> Path:
    """A short tune of sine notes with a soft attack and decay."""
    notes = [(523.25, 0.25), (659.25, 0.25), (783.99, 0.25), (1046.5, 0.5), (783.99, 0.25), (1046.5, 0.75)]
    parts = []
    for frequency, seconds in notes:
        t = np.arange(int(seconds * voice.SAMPLE_RATE)) / voice.SAMPLE_RATE
        envelope = np.minimum(1, t / 0.02) * np.exp(-3 * t)
        parts.append(0.4 * envelope * np.sin(2 * math.pi * frequency * t))
    return voice.write_wav(path, np.concatenate(parts))


def answer(intent: str, now: datetime | None = None) -> dict[str, str]:
    """Answer text of an intent, plus a picture link for `picture`."""
    now = now or datetime.now()
    if intent == "greeting":
        return {"answer": "Hello! I am the voice server of lab six. Ask me the time, the date, a joke, music or a picture."}
    if intent == "time":
        return {"answer": f"It is {now:%H:%M}."}
    if intent == "date":
        return {"answer": f"Today is {now:%A, %B} {now.day}, {now.year}."}
    if intent == "joke":
        return {"answer": JOKES[next(_jokes) % len(JOKES)]}
    if intent == "music":
        return {"answer": "Here is a melody for you."}
    if intent == "picture":
        return {"answer": "Here is a picture drawn by the server.", "image": f"/image?text=Lab+6+{now:%H:%M:%S}"}
    return {"answer": "Sorry, I did not understand."}


def reply(intent: str, margin: float, text: str | None) -> dict[str, object]:
    """Answer text and its WAV; music gets the melody after the words."""
    result: dict[str, object] = {"text": text, "intent": intent, "margin": round(margin, 3), **answer(intent)}
    name = f"answer_{intent}_{uuid.uuid4().hex[:8]}.wav"
    speech = voice.text_to_wav(str(result["answer"]), ANSWERS_DIR / name, voice=SERVER_VOICE if SERVER_VOICE in available_voices() else None)
    if intent == "music":
        _rate, words = voice.read_wav(speech)
        _rate, tune = voice.read_wav(melody(ANSWERS_DIR / f"tune_{name}"))
        voice.write_wav(speech, np.concatenate([words, np.zeros(voice.SAMPLE_RATE // 4, dtype=np.int16), tune]))
        (ANSWERS_DIR / f"tune_{name}").unlink()
    result["audio"] = f"/audio/{name}"
    return result


# ---------------------------------------------------------------- pictures


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("Arial.ttf", "Helvetica.ttc", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def picture(text: str, width: int = 480, height: int = 270) -> bytes:
    """PNG: a sky gradient, a sun, hills and the text."""
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        shade = y / height
        draw.line([(0, y), (width, y)], fill=(int(40 + 120 * shade), int(90 + 110 * shade), 230))
    r = height // 7
    draw.ellipse([width - 3 * r, r, width - r, 3 * r], fill=(255, 214, 0))
    draw.polygon([(0, height), (0, height * 3 // 4), (width // 3, height * 3 // 5), (width * 2 // 3, height * 4 // 5), (width, height * 2 // 3), (width, height)], fill=(46, 139, 87))
    draw.text((24, 24), text, fill="white", font=_font(height // 9))
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def clock_frame(moment: datetime, size: int = 240) -> bytes:
    """JPEG of an analog clock: one frame of the image stream."""
    image = Image.new("RGB", (size, size), (250, 250, 250))
    draw = ImageDraw.Draw(image)
    centre, r = size / 2, size * 0.42
    draw.ellipse([centre - r, centre - r, centre + r, centre + r], outline=(30, 30, 30), width=4)
    for mark in range(12):
        angle = math.radians(mark * 30)
        draw.line([(centre + 0.85 * r * math.sin(angle), centre - 0.85 * r * math.cos(angle)), (centre + r * math.sin(angle), centre - r * math.cos(angle))], fill=(30, 30, 30), width=3)
    hands = [
        ((moment.hour % 12 + moment.minute / 60) * 30, 0.5, 6, (30, 30, 30)),
        ((moment.minute + moment.second / 60) * 6, 0.75, 4, (30, 30, 30)),
        (moment.second * 6, 0.9, 2, (220, 40, 40)),
    ]
    for degrees, length, width, colour in hands:
        angle = math.radians(degrees)
        draw.line([(centre, centre), (centre + length * r * math.sin(angle), centre - length * r * math.cos(angle))], fill=colour, width=width)
    draw.text((centre, size - 14), f"{moment:%H:%M:%S}", fill=(90, 90, 90), font=_font(14), anchor="mm")
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=85)
    return buffer.getvalue()


# ---------------------------------------------------------------- HTTP


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        pass

    def _send(self, status: int, body: bytes, content_type: str, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, data: object, status: int = 200) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message}, status)

    def _body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length > 20 * 1024 * 1024:
            raise ValueError("body over 20 MiB")
        return self.rfile.read(length)

    # ------------------------------------------------------------ GET

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        url = urlparse(self.path)
        path, query = unquote(url.path), parse_qs(url.query)
        if path in ("/", "/index.html"):
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/image":
            self._send(200, picture(query.get("text", ["Lab 6 streaming server"])[0][:60]), "image/png", {"Cache-Control": "no-store"})
        elif path == "/stream-image":
            self._stream_clock(int(query.get("frames", ["0"])[0] or 0))
        elif path.startswith(("/audio/", "/stream/")):
            self._send_wav(path.split("/", 2)[2])
        elif path == "/recordings":
            self._json([{"name": item.name, "url": f"/audio/{item.name}", "info": voice.describe(item)} for item in sorted(RECORDINGS_DIR.glob("*.wav"), reverse=True)])
        else:
            self._error(404, "Endpoint not found")

    def _stream_clock(self, frames: int) -> None:
        """Server push: every second a new JPEG replaces the previous one; `frames=0` streams until the client leaves."""
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        sent = 0
        try:
            while frames == 0 or sent < frames:
                jpeg = clock_frame(datetime.now())
                self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n")
                self.wfile.flush()
                sent += 1
                if frames == 0 or sent < frames:
                    time.sleep(1)
            self.wfile.write(b"--frame--\r\n")
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_wav(self, name: str) -> None:
        if not SAFE_NAME.match(name):
            self._error(400, "bad file name")
            return
        file = next((folder / name for folder in (ANSWERS_DIR, RECORDINGS_DIR) if (folder / name).is_file()), None)
        if file is None:
            self._error(404, "Audio file not found")
            return
        size = file.stat().st_size
        start, end = 0, size - 1
        found = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range", ""))
        if found and (found.group(1) or found.group(2)):
            if found.group(1):
                start = int(found.group(1))
                end = min(int(found.group(2)), size - 1) if found.group(2) else size - 1
            else:
                start = max(0, size - int(found.group(2)))
            if start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
        self.send_response(206 if found else 200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Disposition", f'inline; filename="{name}"')
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if found:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command == "HEAD":
            return
        with file.open("rb") as source:
            source.seek(start)
            left = end - start + 1
            try:
                while left > 0:
                    chunk = source.read(min(CHUNK, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                self.close_connection = True

    # ------------------------------------------------------------ POST

    def do_POST(self) -> None:
        url = urlparse(self.path)
        try:
            body = self._body()
            if url.path == "/ask":
                text = str(json.loads(body or b"{}").get("text", "")).strip()
                if not text:
                    self._error(400, "empty text")
                    return
                query_wav = ANSWERS_DIR / f"query_{uuid.uuid4().hex[:8]}.wav"
                intent, margin = model().classify_text(text, query_wav)
                result = reply(intent, margin, text)
                result["query_audio"] = f"/audio/{query_wav.name}"
                self._json(result)
            elif url.path == "/ask-wav":
                query_wav = voice.write_wav(ANSWERS_DIR / f"query_{uuid.uuid4().hex[:8]}.wav", _wav_samples(body))
                intent, margin = model().predict(query_wav)
                result = reply(intent, margin, None)
                result["query_audio"] = f"/audio/{query_wav.name}"
                self._json(result)
            elif url.path == "/upload":
                name = parse_qs(url.query).get("name", [f"recording_{datetime.now():%Y%m%d_%H%M%S}.wav"])[0]
                name = Path(name).name if name.endswith(".wav") else f"{Path(name).name}.wav"
                if not SAFE_NAME.match(name):
                    self._error(400, "bad file name")
                    return
                saved = voice.write_wav(RECORDINGS_DIR / name, _wav_samples(body))
                self._json({"name": name, "url": f"/audio/{name}", "info": voice.describe(saved)})
            else:
                self._error(404, "Endpoint not found")
        except (ValueError, json.JSONDecodeError) as exc:
            self._error(400, str(exc))


def _wav_samples(payload: bytes) -> np.ndarray:
    """16 kHz mono int16 samples of a WAV body (any rate, mono or stereo)."""
    import wave

    try:
        with wave.open(io.BytesIO(payload), "rb") as wav:
            if wav.getsampwidth() != 2:
                raise ValueError("16-bit PCM WAV expected")
            channels, rate = wav.getnchannels(), wav.getframerate()
            samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)[::channels]
    except wave.Error as exc:
        raise ValueError(f"not a WAV file: {exc}") from exc
    if rate != voice.SAMPLE_RATE:
        import librosa

        samples = (librosa.resample(samples.astype(np.float32) / 32768, orig_sr=rate, target_sr=voice.SAMPLE_RATE) * 32767).astype(np.int16)
    return samples


class VoiceServer:
    def __init__(self, host: str = LAB6_WEB_HOST, port: int = LAB6_WEB_PORT) -> None:
        self.host = host
        self.port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._external = False

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"

    @property
    def running(self) -> bool:
        return self._external or (self._thread is not None and self._thread.is_alive())

    def start(self) -> None:
        if self.running:
            return
        ANSWERS_DIR.mkdir(parents=True, exist_ok=True)
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        except OSError:
            # the port is taken: fine if it is this server already started by `python -m lab6.server`
            import urllib.request

            with urllib.request.urlopen(self.url, timeout=3) as response:
                self._external = b"Lab 6 voice server" in response.read()
            if not self._external:
                raise
            return
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, name="lab6-web", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._external = False
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._server = None
        self._thread = None


def main() -> None:
    server = VoiceServer()
    server.start()
    print(f"Lab 6 server: {server.url} (the classifier is trained on the first question)", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


if __name__ == "__main__":
    main()
