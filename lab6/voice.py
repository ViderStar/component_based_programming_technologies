"""Sound on both sides: text → WAV, microphone → WAV, WAV → speakers, WAV → text.

WAV files are 16-bit PCM mono at 16 kHz everywhere, so the same reader serves the classifier,
the server and the player.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import threading
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16000


class RecognitionError(RuntimeError):
    """Speech was not recognized: silence, noise or no access to the recognition service."""


# ---------------------------------------------------------------- files


def write_wav(path: Path, samples: np.ndarray, rate: int = SAMPLE_RATE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = samples if samples.dtype == np.int16 else (np.clip(samples, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())
    return path


def read_wav(path: Path) -> tuple[int, np.ndarray]:
    """(rate, int16 samples of the first channel)."""
    with wave.open(str(path), "rb") as wav:
        if wav.getsampwidth() != 2:
            raise ValueError(f"{path.name}: {8 * wav.getsampwidth()}-bit samples, 16-bit PCM expected")
        channels, rate = wav.getnchannels(), wav.getframerate()
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
    return rate, samples[::channels].copy()


def describe(path: Path) -> str:
    rate, samples = read_wav(path)
    return f"{path.name}: {rate} Hz, mono, {len(samples) / rate:.1f} s, {path.stat().st_size // 1024} KiB"


# ---------------------------------------------------------------- text → WAV


def tts_available() -> bool:
    if shutil.which("say"):
        return True
    try:
        import pyttsx3  # noqa: F401
    except ImportError:
        return False
    return True


def text_to_wav(text: str, path: Path, voice: str | None = None, rate: int | None = None) -> Path:
    """Synthesize speech into a 16 kHz WAV: `say` on macOS, pyttsx3 (SAPI, eSpeak) elsewhere."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("say"):
        command = ["say", "--data-format=LEI16@16000", "-o", str(path)]
        if voice:
            command += ["-v", voice]
        if rate:
            command += ["-r", str(rate)]
        subprocess.run([*command, "--", text], check=True, capture_output=True, timeout=60)
        return path
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", rate or 150)
    engine.setProperty("volume", 1)
    if voice:
        engine.setProperty("voice", voice)
    engine.save_to_file(text, str(path))
    engine.runAndWait()
    return _resample_file(path)


def voices() -> list[str]:
    """Installed English voices of `say` (empty list without it)."""
    if not shutil.which("say") or platform.system() != "Darwin":
        return []
    listing = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, timeout=30).stdout
    names = []
    for line in listing.splitlines():
        name, _sep, rest = line.partition("#")[0].rstrip().rpartition(" ")
        if rest.startswith("en_") and name.strip():
            names.append(name.strip())
    return names


def _resample_file(path: Path) -> Path:
    import librosa

    samples, _rate = librosa.load(str(path), sr=SAMPLE_RATE, mono=True)
    return write_wav(path, samples)


# ---------------------------------------------------------------- microphone and speakers


class Recorder:
    """Record from the default microphone between `start()` and `stop()`."""

    def __init__(self, rate: int = SAMPLE_RATE) -> None:
        self.rate = rate
        self._chunks: list[np.ndarray] = []
        self._stream = None

    @property
    def recording(self) -> bool:
        return self._stream is not None

    @property
    def seconds(self) -> float:
        return sum(len(chunk) for chunk in self._chunks) / self.rate

    def start(self) -> None:
        import sounddevice as sd

        self._chunks = []
        self._stream = sd.InputStream(samplerate=self.rate, channels=1, dtype="int16", callback=self._collect)
        self._stream.start()

    def _collect(self, data: np.ndarray, _frames: int, _time: object, _status: object) -> None:
        self._chunks.append(data[:, 0].copy())

    def stop(self, path: Path) -> Path:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        samples = np.concatenate(self._chunks) if self._chunks else np.zeros(0, dtype=np.int16)
        return write_wav(path, samples, self.rate)


def record(seconds: float, path: Path) -> Path:
    import sounddevice as sd

    samples = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    return write_wav(path, samples[:, 0])


def has_microphone() -> bool:
    try:
        import sounddevice as sd

        return sd.query_devices(kind="input") is not None
    except Exception:
        return False


_PLAYING = threading.Event()


def play(path: Path, wait: bool = True) -> None:
    """Play a WAV in chunks of 1024 frames, like the PyAudio program of the handout."""
    import sounddevice as sd

    rate, samples = read_wav(path)
    _PLAYING.set()

    def stream() -> None:
        with sd.OutputStream(samplerate=rate, channels=1, dtype="int16") as out:
            for start in range(0, len(samples), 1024):
                if not _PLAYING.is_set():
                    break
                out.write(samples[start : start + 1024].reshape(-1, 1))
        _PLAYING.clear()

    if wait:
        stream()
    else:
        threading.Thread(target=stream, name="lab6-play", daemon=True).start()


def stop_playback() -> None:
    _PLAYING.clear()


# ---------------------------------------------------------------- WAV → text


def recognize(path: Path, language: str = "en-US") -> str:
    """Speech to text with the free Google Web Speech API of `speech_recognition`."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with sr.AudioFile(str(path)) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.2)  # the default 1 s would eat a short phrase
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError as exc:
        raise RecognitionError("speech not understood") from exc
    except sr.RequestError as exc:
        raise RecognitionError(f"Google Speech Recognition unavailable: {exc}") from exc
