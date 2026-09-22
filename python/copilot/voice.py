from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True)
class VoiceConfig:
    stt_model: str = "small"
    stt_device: str = "auto"
    sample_rate: int = 16000
    seconds_per_utterance: float = 4.0


class VoiceLoop:
    """Optional local voice adapter.

    This intentionally uses bounded utterance capture as a reference implementation.
    Production builds should replace it with VAD/endpointing and streaming partial STT.
    """

    def __init__(self, cfg: VoiceConfig, on_text: Callable[[str], str]) -> None:
        self.cfg = cfg
        self.on_text = on_text
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._tts_queue: queue.Queue[str] = queue.Queue(maxsize=8)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="voice-loop", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        try:
            import numpy as np
            import sounddevice as sd
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("Install voice extras: pip install -e '.[voice]'") from exc

        device = None if self.cfg.stt_device == "auto" else self.cfg.stt_device
        model = WhisperModel(self.cfg.stt_model, device=device or "auto", compute_type="int8")
        frames = int(self.cfg.sample_rate * self.cfg.seconds_per_utterance)

        while not self._stop.is_set():
            audio = sd.rec(frames, samplerate=self.cfg.sample_rate, channels=1, dtype="float32")
            sd.wait()
            mono = np.squeeze(audio)
            segments, _ = model.transcribe(mono, language=None, vad_filter=True, beam_size=1)
            text = " ".join(seg.text.strip() for seg in segments).strip()
            if text:
                response = self.on_text(text)
                if response:
                    self.speak(response)

    def speak(self, text: str) -> None:
        # System TTS fallback. A production installation can replace this with
        # a Piper-compatible local backend and configured voice files.
        try:
            import pyttsx3
        except ImportError:
            return
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
