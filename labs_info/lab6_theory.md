# Lab 6: Streaming web servers and a voice assistant

## Terms

| Term | Meaning |
| --- | --- |
| `http.server` | the standard-library HTTP server: `BaseHTTPRequestHandler.do_GET`/`do_POST` write the status, headers and body into `wfile` |
| streaming | the body is written in chunks while it is read or generated, not built in memory first |
| `multipart/x-mixed-replace` | server push of images: each part replaces the previous one in `<img>`, so a JPEG per second becomes a live picture |
| `Range: bytes=a-b` → `206 Partial Content` | the browser's `<audio>` asks for parts of a file to seek; Safari and WebKit need it |
| WAV | RIFF header (44 bytes) + PCM samples; here 16-bit, mono, 16 kHz |
| TTS | text to speech: `say` on macOS, pyttsx3 (SAPI, eSpeak) elsewhere |
| speech recognition | `speech_recognition.Recognizer().recognize_google`: the free Google Web Speech API, needs the internet |
| MFCC | mel-frequency cepstral coefficients: FFT of 2048-sample windows → mel filter bank → log → DCT, 13 numbers per window |
| SVM | support vector machine; `SVC` of scikit-learn |

## The loop of the handout

```
client                                         server (lab6/server.py, port 8050)
microphone ─► recording.wav (sounddevice)
recording.wav ─► text (Google Web Speech)
text ── POST /ask {"text"} ──────────────────► text ─► query.wav (TTS, server voice)
                                               query.wav ─► MFCC ─► SVM ─► intent
                                               intent ─► answer text ─► answer.wav (TTS, + melody for music)
answer.wav ◄── GET /audio/answer_….wav ─────── 16 KiB chunks, Range
speakers ◄── answer.wav (1024-frame chunks)
```

Without the internet the client sends the recording itself (`POST /ask-wav`), and the server classifies it directly.

## Classifier

- Six intents (`greeting`, `time`, `date`, `joke`, `music`, `picture`), six phrasings each, spoken by eight `say` voices: 288 WAVs in `artifacts/lab6/dataset/`.
- Features: silence trimmed, MFCC (13 × frames); mean, spread and mean change over the phrase plus the mean of its three thirds, 78 numbers.
- Model: `StandardScaler` + `SVC(kernel="rbf", C=3)`, saved to `artifacts/lab6/model.pkl` and retrained when the intents or the voices change.

| Model | Unseen voice | Unseen phrasing |
| --- | --- | --- |
| handout: mean MFCC + linear SVC | 43% | 40% |
| 78 features + linear SVC | 55% | 43% |
| this lab: 78 features + RBF SVC | 60% | 53% |

Chance is 17%. The server always speaks with one voice, so the phrasing is what varies; the phrasings of the training set are recognized every time.

## Recording and listening

- `voice.Recorder`: `sounddevice.InputStream` collects int16 chunks between `start()` and `stop(path)`, the WAV goes to `artifacts/lab6/client/`.
- `voice.play`: reads the WAV and writes it to `sounddevice.OutputStream` in 1024-frame chunks, like the PyAudio program of the handout.
- The page `http://127.0.0.1:8050/` records in the browser: `getUserMedia` → `ScriptProcessor` → 16-bit PCM WAV in JavaScript → `POST /upload`, and plays every recording with `<audio>`.
