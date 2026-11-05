"""Checkable scenarios of Lab 6: TTS dataset, classifier, image streaming, WAV upload and streaming, the voice dialog."""

from __future__ import annotations

import io
import json
import urllib.request
from datetime import datetime

import numpy as np
from PIL import Image

from lab6 import classifier, voice
from lab6.classifier import DATA_DIR, INTENTS
from lab6.client import VoiceClient
from lab6.server import VoiceServer

_SERVER: VoiceServer | None = None
CASES_DIR = DATA_DIR / "cases"


def ensure_server() -> VoiceServer:
    global _SERVER
    if _SERVER is None or not _SERVER.running:
        _SERVER = VoiceServer()
        _SERVER.start()
    return _SERVER


def stop_server() -> None:
    global _SERVER
    if _SERVER is not None:
        _SERVER.stop()
        _SERVER = None


def client() -> VoiceClient:
    return VoiceClient(ensure_server().url)


def _get(path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(ensure_server().url.rstrip("/") + path, headers=headers or {})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, dict(response.headers), response.read()


# ---------------------------------------------------------------- cases


def tts_dataset() -> str:
    if not voice.tts_available():
        raise RuntimeError("no text-to-speech engine: `say` (macOS) or pyttsx3")
    samples = classifier.build_dataset()
    lengths = [voice.read_wav(sample.path)[1].size / voice.SAMPLE_RATE for sample in samples]
    if min(lengths) < 0.2:
        raise AssertionError(f"a WAV of {min(lengths):.2f} s")
    voices = len({sample.voice for sample in samples})
    return f"{len(samples)} WAVs = {len(INTENTS)} intents × {len(samples) // len(INTENTS) // voices} phrasings × {voices} voices, {min(lengths):.1f}–{max(lengths):.1f} s"


def mfcc_features() -> str:
    sample = classifier.build_dataset()[0]
    frames = classifier.mfcc(sample.path)
    vector = classifier.features(sample.path)
    if frames.shape[1] != classifier.N_MFCC or vector.shape != (classifier.N_MFCC * (3 + classifier.SEGMENTS),):
        raise AssertionError((frames.shape, vector.shape))
    return f"{sample.path.name}: MFCC {frames.shape[0]} frames × {frames.shape[1]}, feature vector of {vector.size}"


def classifier_accuracy() -> str:
    model = classifier.IntentClassifier.load()
    if model.report.train_accuracy < 0.9 or model.report.unseen_phrase < 0.35:
        raise AssertionError(str(model.report))
    return str(model.report)


def image_endpoints() -> str:
    status, headers, png = _get("/image?text=Hello")
    picture = Image.open(io.BytesIO(png))
    if headers["Content-Type"] != "image/png" or picture.format != "PNG":
        raise AssertionError(headers["Content-Type"])
    _status, headers, stream = _get("/stream-image?frames=3")
    if not headers["Content-Type"].startswith("multipart/x-mixed-replace"):
        raise AssertionError(headers["Content-Type"])
    frames = [part for part in stream.split(b"--frame") if b"image/jpeg" in part]
    for part in frames:
        Image.open(io.BytesIO(part.split(b"\r\n\r\n", 1)[1])).verify()
    if len(frames) != 3:
        raise AssertionError(f"{len(frames)} frames")
    return f"/image: PNG {picture.size[0]}×{picture.size[1]}; /stream-image: {len(frames)} JPEG frames in multipart/x-mixed-replace"


def wav_upload_and_stream() -> str:
    """A WAV goes up (like a microphone recording), comes back whole and by `Range`, and is listed."""
    t = np.arange(voice.SAMPLE_RATE) / voice.SAMPLE_RATE
    local = voice.write_wav(CASES_DIR / "tone_440.wav", 0.3 * np.sin(2 * np.pi * 440 * t))
    saved = client().upload(local)
    downloaded = client().download(saved["url"], CASES_DIR / "downloaded")
    if downloaded.read_bytes() != local.read_bytes():
        raise AssertionError("the WAV came back changed")
    status, headers, part = _get(saved["url"], {"Range": "bytes=0-43"})
    if status != 206 or part[:4] != b"RIFF" or len(part) != 44 or not headers["Content-Range"].startswith("bytes 0-43/"):
        raise AssertionError((status, headers.get("Content-Range"), len(part)))
    _status, _headers, listing = _get("/recordings")
    if saved["name"] not in [item["name"] for item in json.loads(listing)]:
        raise AssertionError("the upload is not in /recordings")
    return f"{saved['info']}; same bytes back; Range 0-43 → 206 with the RIFF header; listed in /recordings"


def ask_by_text() -> str:
    voice_client = client()
    right = 0
    for intent, phrases in INTENTS.items():
        reply = voice_client.ask_text(phrases[0])
        right += reply["intent"] == intent
        answer = voice_client.download(reply["audio"], CASES_DIR / "answers")
        if voice.read_wav(answer)[1].size < voice.SAMPLE_RATE // 2:
            raise AssertionError(f"{intent}: answer WAV too short")
    if right < len(INTENTS) - 1:
        raise AssertionError(f"only {right}/{len(INTENTS)} intents recognized")
    reply = voice_client.ask_text("what time is it")
    if reply["intent"] != "time" or f"{datetime.now():%H}" not in reply["answer"]:
        raise AssertionError(reply)
    return f"{right}/{len(INTENTS)} intents by their first phrasing; time → “{reply['answer']}” + answer WAV"


def speech_recognition() -> str:
    """WAV → text with Google Web Speech: needs the internet."""
    wav = voice.text_to_wav("tell me a joke", CASES_DIR / "speech.wav", voice="Daniel" if "Daniel" in voice.voices() else None)
    try:
        text = voice.recognize(wav)
    except voice.RecognitionError as exc:
        return f"skipped: {exc}"
    if "joke" not in text.lower():
        raise AssertionError(text)
    return f"{wav.name} → “{text}”"


def voice_dialog() -> str:
    """The whole loop of the handout with a TTS voice in place of the microphone."""
    wav = voice.text_to_wav("play some music", CASES_DIR / "question.wav", voice="Daniel" if "Daniel" in voice.voices() else None)
    reply, answer = client().converse(wav)
    if reply["intent"] != "music":
        raise AssertionError(reply)
    route = f"recognized “{reply['text']}”" if reply.get("text") else f"offline ({reply.get('recognition')}), WAV classified"
    return f"{route} → {reply['intent']} → {voice.describe(answer)}"


def audio_devices() -> str:
    import sounddevice as sd

    try:
        source, sink = sd.query_devices(kind="input"), sd.query_devices(kind="output")
    except Exception as exc:
        return f"skipped: {exc}"
    return f"microphone: {source['name']}; speakers: {sink['name']}"
