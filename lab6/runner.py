"""CLI demo for the streaming voice server: dataset, classifier, images, WAV streaming, the dialog."""

from __future__ import annotations

import logging

from lab6 import cases, voice

logger = logging.getLogger(__name__)

CASES = (
    ("tts_dataset", cases.tts_dataset),
    ("mfcc_features", cases.mfcc_features),
    ("classifier_accuracy", cases.classifier_accuracy),
    ("image_endpoints", cases.image_endpoints),
    ("wav_upload_and_stream", cases.wav_upload_and_stream),
    ("ask_by_text", cases.ask_by_text),
    ("speech_recognition", cases.speech_recognition),
    ("voice_dialog", cases.voice_dialog),
    ("audio_devices", cases.audio_devices),
)


def run_lab6() -> dict[str, str]:
    if not voice.tts_available():
        logger.info("Lab 6 skipped: no text-to-speech engine")
        return {"skipped": "no text-to-speech engine"}
    results: dict[str, str] = {}
    try:
        for name, case in CASES:
            results[name] = case()
            logger.info("%s -> %s", name, results[name])
    finally:
        cases.stop_server()
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_lab6()
