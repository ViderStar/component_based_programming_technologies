"""WAV classifier of requests: TTS training set → MFCC features → SVM.

Every intent has several phrasings; each phrasing is spoken by several `say` voices, so the model
learns the sound of a request, not one recording. The server speaks the text it receives with
`SERVER_VOICE` and classifies that WAV.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from configs.cfg import ARTIFACTS_DIR
from lab6 import voice

DATA_DIR = ARTIFACTS_DIR / "lab6"
DATASET_DIR = DATA_DIR / "dataset"
MODEL_PATH = DATA_DIR / "model.pkl"

INTENTS: dict[str, list[str]] = {
    "greeting": ["hello", "hi there", "good morning", "hello server", "hey, how are you", "nice to meet you"],
    "time": ["what time is it", "tell me the time", "what is the time now", "current time please", "do you know the time", "what's the time"],
    "date": ["what is the date today", "what day is it", "tell me today's date", "which date is it today", "what is today", "give me the date"],
    "joke": ["tell me a joke", "make me laugh", "say something funny", "do you know a joke", "another joke please", "I want a joke"],
    "music": ["play some music", "play a song", "I want to hear music", "turn on the music", "sing a melody", "play a tune"],
    "picture": ["show me a picture", "draw an image", "send me a photo", "I want to see a picture", "show the image", "paint something"],
}
TRAIN_VOICES = ["Samantha", "Daniel", "Karen", "Moira", "Tessa", "Rishi", "Fred", "Albert"]
SERVER_VOICE = "Samantha"

N_MFCC = 13
SEGMENTS = 3


def mfcc(path: Path) -> np.ndarray:
    """MFCC matrix (frames × 13) of a WAV after the silence around the speech is cut off."""
    import librosa

    audio, rate = librosa.load(str(path), sr=voice.SAMPLE_RATE)
    trimmed, _bounds = librosa.effects.trim(audio, top_db=30)
    if len(trimmed) < 2048:
        trimmed = np.pad(trimmed if len(trimmed) else audio, (0, 2048))
    return librosa.feature.mfcc(y=trimmed, sr=rate, n_mfcc=N_MFCC, n_fft=2048, hop_length=512).T


def features(path: Path) -> np.ndarray:
    """One vector per WAV (78 numbers): mean, spread and mean change of the MFCC over the whole phrase,
    plus the mean MFCC of its beginning, middle and end, so the order of the sounds is not lost."""
    frames = mfcc(path)
    delta = np.diff(frames, axis=0) if len(frames) > 1 else np.zeros_like(frames)
    thirds = [part.mean(axis=0) for part in np.array_split(frames, SEGMENTS)]
    return np.concatenate([frames.mean(axis=0), frames.std(axis=0), np.abs(delta).mean(axis=0), *thirds])


# ---------------------------------------------------------------- dataset


@dataclass(frozen=True)
class Sample:
    intent: str
    phrase: int
    voice: str
    path: Path


def available_voices() -> list[str]:
    installed = set(voice.voices())
    chosen = [name for name in TRAIN_VOICES if name in installed]
    return chosen or [""]  # "" = the default voice of the engine


def _sample_path(intent: str, phrase: int, speaker: str) -> Path:
    return DATASET_DIR / intent / f"{phrase}_{(speaker or 'default').replace(' ', '_')}.wav"


def build_dataset() -> list[Sample]:
    """Speak every phrasing with every voice; WAVs already on disk are reused."""
    samples = [
        Sample(intent, index, speaker, _sample_path(intent, index, speaker))
        for intent, phrases in INTENTS.items()
        for index, _text in enumerate(phrases)
        for speaker in available_voices()
    ]
    missing = [sample for sample in samples if not sample.path.exists()]

    def speak(sample: Sample) -> None:
        voice.text_to_wav(INTENTS[sample.intent][sample.phrase], sample.path, voice=sample.voice or None)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(speak, missing))
    return samples


# ---------------------------------------------------------------- model


def _pipeline():
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC

    # the handout's linear SVC on mean MFCC: 43% on an unseen voice, 40% on an unseen phrasing;
    # these features with an RBF kernel: 60% and 53% (6 intents, chance 17%)
    return make_pipeline(StandardScaler(), SVC(kernel="rbf", C=3.0))


def _fingerprint() -> str:
    return hashlib.sha1(json.dumps([INTENTS, available_voices(), N_MFCC, SEGMENTS, repr(_pipeline())]).encode()).hexdigest()[:12]


@dataclass
class Report:
    samples: int
    voices: int
    train_accuracy: float
    unseen_voice: float
    unseen_phrase: float

    def __str__(self) -> str:
        return (
            f"{self.samples} WAVs, {len(INTENTS)} intents, {self.voices} voices; accuracy: train {self.train_accuracy:.0%}, "
            f"unseen voice {self.unseen_voice:.0%}, unseen phrasing {self.unseen_phrase:.0%}"
        )


class IntentClassifier:
    def __init__(self, model, report: Report, fingerprint: str) -> None:
        self.model = model
        self.report = report
        self.fingerprint = fingerprint

    @classmethod
    def train(cls) -> IntentClassifier:
        from sklearn.model_selection import GroupKFold, cross_val_score

        samples = build_dataset()
        x = np.array([features(sample.path) for sample in samples])
        y = np.array([sample.intent for sample in samples])
        by_voice = np.array([sample.voice for sample in samples])
        by_phrase = np.array([sample.phrase for sample in samples])
        speakers = len(set(by_voice))
        unseen_voice = (
            cross_val_score(_pipeline(), x, y, groups=by_voice, cv=GroupKFold(n_splits=min(4, speakers))).mean()
            if speakers > 1
            else float("nan")
        )
        unseen_phrase = cross_val_score(_pipeline(), x, y, groups=by_phrase, cv=GroupKFold(n_splits=3)).mean()
        model = _pipeline().fit(x, y)
        report = Report(len(samples), speakers, model.score(x, y), unseen_voice, unseen_phrase)
        return cls(model, report, _fingerprint())

    @classmethod
    def load(cls) -> IntentClassifier:
        """The saved model, or a new one when the intents or the voices changed."""
        if MODEL_PATH.exists():
            with MODEL_PATH.open("rb") as file:
                saved = pickle.load(file)
            if isinstance(saved, cls) and saved.fingerprint == _fingerprint():
                return saved
        trained = cls.train()
        trained.save()
        return trained

    def save(self) -> Path:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with MODEL_PATH.open("wb") as file:
            pickle.dump(self, file)
        return MODEL_PATH

    def predict(self, path: Path) -> tuple[str, float]:
        """(intent, margin): the margin is how far the winner's SVM score is ahead of the runner-up."""
        vector = features(path).reshape(1, -1)
        scores = self.model.decision_function(vector)[0]
        ranked = np.sort(scores)
        return str(self.model.predict(vector)[0]), float(ranked[-1] - ranked[-2])

    def classify_text(self, text: str, path: Path) -> tuple[str, float]:
        """The server side of the handout: text → WAV with the server voice → classifier."""
        voice.text_to_wav(text, path, voice=SERVER_VOICE if SERVER_VOICE in available_voices() else None)
        return self.predict(path)
