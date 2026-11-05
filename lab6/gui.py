"""Lab 6 window: record a WAV, listen to it, send it to the voice server and listen to the answer."""

from __future__ import annotations

import threading
from pathlib import Path

import wx
import wx.html2

from helpers.office import open_path
from lab6 import cases, voice
from lab6.client import CLIENT_DIR, new_recording_path
from ui.cases import CasePanel
from ui.theme import MUTED, PAGE_BG, append_log, apply_window_icon, make_header, make_log, styled_button


class VoicePanel(wx.Panel):
    """Microphone → WAV → speakers, and the dialog with the server."""

    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent)
        self.SetBackgroundColour(wx.WHITE)
        self.recorder = voice.Recorder()
        self.answer_wav: Path | None = None
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_tick, self.timer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._caption("Record a WAV"), 0, wx.ALL, 10)
        row = wx.BoxSizer(wx.HORIZONTAL)
        self.record_button = styled_button(self, "● Record")
        self.stop_button = styled_button(self, "■ Stop", primary=False)
        play = styled_button(self, "▶ Play", primary=False)
        silence = styled_button(self, "Mute", primary=False)
        ask = styled_button(self, "Ask the server")
        upload = styled_button(self, "Upload", primary=False)
        folder = styled_button(self, "Folder", primary=False)
        self.record_button.Bind(wx.EVT_BUTTON, self._on_record)
        self.stop_button.Bind(wx.EVT_BUTTON, self._on_stop)
        play.Bind(wx.EVT_BUTTON, lambda _e: self._play(self._selected()))
        silence.Bind(wx.EVT_BUTTON, lambda _e: voice.stop_playback())
        ask.Bind(wx.EVT_BUTTON, self._on_ask_wav)
        upload.Bind(wx.EVT_BUTTON, self._on_upload)
        folder.Bind(wx.EVT_BUTTON, lambda _e: open_path(CLIENT_DIR))
        for button in (self.record_button, self.stop_button, play, silence, ask, upload, folder):
            row.Add(button, 0, wx.RIGHT, 6)
        self.stop_button.Disable()
        sizer.Add(row, 0, wx.LEFT | wx.RIGHT, 10)

        self.state = wx.StaticText(self, label="Select a recording and press Play, or record a new one.")
        self.state.SetForegroundColour(MUTED)
        sizer.Add(self.state, 0, wx.ALL, 10)
        self.recordings = wx.ListBox(self, size=(-1, 140))
        self.recordings.Bind(wx.EVT_LISTBOX_DCLICK, lambda _e: self._play(self._selected()))
        sizer.Add(self.recordings, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        sizer.Add(self._caption("Ask by text"), 0, wx.ALL, 10)
        row = wx.BoxSizer(wx.HORIZONTAL)
        self.question = wx.TextCtrl(self, value="tell me a joke", style=wx.TE_PROCESS_ENTER)
        self.question.Bind(wx.EVT_TEXT_ENTER, self._on_ask_text)
        send = styled_button(self, "Ask")
        send.Bind(wx.EVT_BUTTON, self._on_ask_text)
        replay = styled_button(self, "▶ Answer", primary=False)
        replay.Bind(wx.EVT_BUTTON, lambda _e: self._play(self.answer_wav))
        row.Add(self.question, 1, wx.RIGHT, 6)
        row.Add(send, 0, wx.RIGHT, 6)
        row.Add(replay, 0)
        sizer.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        hint = wx.StaticText(self, label="hello · what time is it · what is the date today · tell me a joke · play some music · show me a picture")
        hint.SetForegroundColour(MUTED)
        sizer.Add(hint, 0, wx.ALL, 10)

        self.reply = wx.StaticText(self, label="")
        self.reply.SetFont(wx.Font(13, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.reply, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        self.picture = wx.StaticBitmap(self)
        sizer.Add(self.picture, 0, wx.ALL, 10)
        self.log = make_log(self, height=110)
        sizer.Add(self.log, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(sizer)
        self.refresh_recordings()

    def _caption(self, label: str) -> wx.StaticText:
        caption = wx.StaticText(self, label=label)
        caption.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        return caption

    # ------------------------------------------------------------ recordings

    def refresh_recordings(self, select: Path | None = None) -> None:
        CLIENT_DIR.mkdir(parents=True, exist_ok=True)
        self.files = sorted(CLIENT_DIR.glob("recording_*.wav"), reverse=True)
        self.recordings.Set([voice.describe(path) for path in self.files])
        if self.files:
            self.recordings.SetSelection(self.files.index(select) if select in self.files else 0)

    def _selected(self) -> Path | None:
        index = self.recordings.GetSelection()
        return self.files[index] if index != wx.NOT_FOUND else None

    def _on_record(self, _event: wx.Event) -> None:
        try:
            self.recorder.start()
        except Exception as exc:
            append_log(self.log, f"microphone: {exc}")
            return
        self.record_button.Disable()
        self.stop_button.Enable()
        self.timer.Start(100)

    def _on_tick(self, _event: wx.TimerEvent) -> None:
        self.state.SetLabel(f"● recording… {self.recorder.seconds:.1f} s")

    def _on_stop(self, _event: wx.Event) -> None:
        self.timer.Stop()
        path = self.recorder.stop(new_recording_path())
        self.record_button.Enable()
        self.stop_button.Disable()
        self.state.SetLabel(f"saved {path}")
        append_log(self.log, f"recorded {voice.describe(path)}")
        self.refresh_recordings(select=path)

    def _play(self, path: Path | None) -> None:
        if path is None or not path.exists():
            return
        voice.stop_playback()
        try:
            voice.play(path, wait=False)
        except Exception as exc:
            append_log(self.log, f"play: {exc}")
            return
        self.state.SetLabel(f"▶ {path.name}")

    # ------------------------------------------------------------ server

    def _background(self, title: str, work, done) -> None:
        """Run network and ML work off the GUI thread."""
        self.state.SetLabel(f"{title}… (the first question trains the classifier)")

        def target() -> None:
            try:
                result = work()
            except Exception as exc:
                wx.CallAfter(append_log, self.log, f"{title}: {exc}")
                wx.CallAfter(self.state.SetLabel, f"{title} failed")
                return
            wx.CallAfter(done, result)

        threading.Thread(target=target, name="lab6-gui", daemon=True).start()

    def _on_ask_wav(self, _event: wx.Event) -> None:
        wav = self._selected()
        if wav is not None:
            self._background(f"asking with {wav.name}", lambda: cases.client().converse(wav), self._show)

    def _on_ask_text(self, _event: wx.Event) -> None:
        text = self.question.GetValue().strip()
        if not text:
            return

        def work() -> tuple[dict, Path]:
            voice_client = cases.client()
            reply = voice_client.ask_text(text)
            return reply, voice_client.download(reply["audio"])

        self._background("asking", work, self._show)

    def _on_upload(self, _event: wx.Event) -> None:
        wav = self._selected()
        if wav is not None:
            self._background(f"uploading {wav.name}", lambda: cases.client().upload(wav), lambda saved: append_log(self.log, f"uploaded {saved['info']} → {saved['url']}"))

    def _show(self, result: tuple[dict, Path]) -> None:
        reply, answer = result
        self.answer_wav = answer
        heard = f"“{reply['text']}”" if reply.get("text") else f"WAV ({reply.get('recognition', 'no text')})"
        self.reply.SetLabel(f"{heard} → {reply['intent']}\n{reply['answer']}")
        self.reply.Wrap(max(300, self.GetSize().width - 30))
        append_log(self.log, f"{heard} → {reply['intent']} (margin {reply['margin']}), {voice.describe(answer)}")
        self.picture.SetBitmap(wx.NullBitmap)
        if reply.get("image"):
            self._load_picture(str(reply["image"]))
        self.state.SetLabel(f"▶ {answer.name}")
        self._play(answer)
        self.Layout()

    def _load_picture(self, url: str) -> None:
        import io
        import urllib.request

        with urllib.request.urlopen(cases.ensure_server().url.rstrip("/") + url, timeout=10) as response:
            image = wx.Image(io.BytesIO(response.read()), wx.BITMAP_TYPE_PNG)
        self.picture.SetBitmap(wx.Bitmap(image.Scale(320, 180, wx.IMAGE_QUALITY_HIGH)))


class Lab6Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="Lab 6", size=(1280, 820))
        apply_window_icon(self)
        cases.ensure_server()
        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "Lab 6  Streaming voice server"), 0, wx.EXPAND)

        body = wx.BoxSizer(wx.HORIZONTAL)
        self.notebook = wx.Notebook(root)
        notebook = self.notebook
        self.voice = VoicePanel(notebook)
        notebook.AddPage(self.voice, "Voice")
        page = wx.Panel(notebook)
        page_sizer = wx.BoxSizer(wx.VERTICAL)
        row = wx.BoxSizer(wx.HORIZONTAL)
        url = wx.StaticText(page, label=cases.ensure_server().url)
        url.SetForegroundColour(MUTED)
        external = styled_button(page, "Open in browser", primary=False)
        external.Bind(wx.EVT_BUTTON, lambda _e: open_path(cases.ensure_server().url))
        row.Add(url, 1, wx.ALIGN_CENTER_VERTICAL)
        row.Add(external, 0)
        page_sizer.Add(row, 0, wx.EXPAND | wx.ALL, 6)
        try:
            self.browser: wx.html2.WebView | None = wx.html2.WebView.New(page, url=cases.ensure_server().url)
        except Exception:
            self.browser = None
        page_sizer.Add(self.browser or wx.StaticText(page, label="No web view available: use “Open in browser”."), 1, wx.EXPAND)
        page.SetSizer(page_sizer)
        notebook.AddPage(page, "Web page")
        body.Add(notebook, 1, wx.EXPAND | wx.ALL, 8)

        self.cases = CasePanel(
            root,
            [
                ("TTS dataset", cases.tts_dataset),
                ("MFCC features", cases.mfcc_features),
                ("classifier", cases.classifier_accuracy),
                ("image + stream", cases.image_endpoints),
                ("WAV upload + stream", cases.wav_upload_and_stream),
                ("ask by text", cases.ask_by_text),
                ("speech recognition", cases.speech_recognition),
                ("voice dialog", cases.voice_dialog),
                ("audio devices", cases.audio_devices),
            ],
        )
        body.Add(self.cases, 0, wx.EXPAND | wx.ALL, 8)
        layout.Add(body, 1, wx.EXPAND)
        root.SetSizer(layout)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Centre()

    def _on_close(self, event: wx.CloseEvent) -> None:
        voice.stop_playback()
        cases.stop_server()
        event.Skip()
