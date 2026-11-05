"""Voice client: record → recognize → send the text → download the answer WAV → play it.

`python -m lab6.client` records 4 s from the microphone; `python -m lab6.client --wav file.wav` takes a file;
`python -m lab6.client --text "tell me a joke"` skips the microphone.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime
from pathlib import Path

from configs.cfg import LAB6_WEB_HOST, LAB6_WEB_PORT
from lab6 import voice
from lab6.classifier import DATA_DIR

CLIENT_DIR = DATA_DIR / "client"


class VoiceClient:
    def __init__(self, base_url: str = f"http://{LAB6_WEB_HOST}:{LAB6_WEB_PORT}") -> None:
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, body: bytes, content_type: str) -> dict:
        request = urllib.request.Request(self.base_url + path, data=body, headers={"Content-Type": content_type}, method="POST")
        with urllib.request.urlopen(request, timeout=600) as response:
            return json.loads(response.read())

    def ask_text(self, text: str) -> dict:
        return self._post("/ask", json.dumps({"text": text}).encode(), "application/json")

    def ask_wav(self, path: Path) -> dict:
        return self._post("/ask-wav", path.read_bytes(), "audio/wav")

    def upload(self, path: Path) -> dict:
        return self._post(f"/upload?name={path.name}", path.read_bytes(), "audio/wav")

    def download(self, url: str, folder: Path = CLIENT_DIR) -> Path:
        """Fetch a WAV of the server chunk by chunk into a local file."""
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / url.rsplit("/", 1)[-1]
        with urllib.request.urlopen(self.base_url + url, timeout=60) as response, target.open("wb") as file:
            if response.headers["Content-Type"] != "audio/wav":
                raise ValueError(f"{url}: {response.headers['Content-Type']}")
            while chunk := response.read(16 * 1024):
                file.write(chunk)
        return target

    def converse(self, wav: Path) -> tuple[dict, Path]:
        """Speech in a WAV → text on the client → answer of the server, saved locally.

        Without the recognition service the WAV itself goes to the server (`/ask-wav`).
        """
        try:
            reply = self.ask_text(voice.recognize(wav))
        except voice.RecognitionError as exc:
            reply = self.ask_wav(wav)
            reply["recognition"] = str(exc)
        return reply, self.download(str(reply["audio"]))


def new_recording_path() -> Path:
    return CLIENT_DIR / f"recording_{datetime.now():%Y%m%d_%H%M%S}.wav"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default=f"http://{LAB6_WEB_HOST}:{LAB6_WEB_PORT}")
    parser.add_argument("--seconds", type=float, default=4.0)
    parser.add_argument("--wav", type=Path)
    parser.add_argument("--text")
    args = parser.parse_args()
    client = VoiceClient(args.url)
    if args.text:
        reply = client.ask_text(args.text)
        answer = client.download(str(reply["audio"]))
    else:
        wav = args.wav
        if wav is None:
            print(f"Speak for {args.seconds:.0f} s…", flush=True)
            wav = voice.record(args.seconds, new_recording_path())
            print(voice.describe(wav))
            voice.play(wav)
        reply, answer = client.converse(wav)
    print(f"text: {reply.get('text')!r} -> intent {reply['intent']} (margin {reply['margin']}): {reply['answer']}")
    voice.play(answer)


if __name__ == "__main__":
    main()
