from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
from threading import Event, Thread
from typing import Dict, Optional

from pc_control.core.config import VoiceConfig
from pc_control.core.models import Command


@dataclass(slots=True)
class VoicePhrase:
    text: str
    confidence: float = 1.0


class VoiceCommandMapper:
    def __init__(self) -> None:
        self.map_table: Dict[str, Command] = {
            "volume up": Command(name="system.volume.up", source="voice"),
            "volume down": Command(name="system.volume.down", source="voice"),
            "mute": Command(name="system.mute.toggle", source="voice"),
            "left click": Command(name="mouse.click.left", source="voice"),
            "right click": Command(name="mouse.click.right", source="voice"),
            "double click": Command(name="mouse.double_click", source="voice"),
            "scroll up": Command(name="mouse.scroll.up", source="voice", payload={"scroll_delta": 120}),
            "scroll down": Command(name="mouse.scroll.down", source="voice", payload={"scroll_delta": -120}),
            "lock computer": Command(name="system.lock", source="voice"),
        }

    def to_command(self, phrase: VoicePhrase) -> Optional[Command]:
        normalized = phrase.text.strip().lower()
        for key, command in self.map_table.items():
            if key in normalized:
                return command
        return None


class SpeechRecognitionListener:
    def __init__(self, config: VoiceConfig) -> None:
        self.config = config
        self.outbox: Queue[VoicePhrase] = Queue()
        self._stop = Event()
        self._worker: Thread | None = None

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        if not self.config.enabled:
            return
        self._stop.clear()
        self._worker = Thread(target=self._loop, daemon=True, name="voice-listener")
        self._worker.start()

    def stop(self) -> None:
        self._stop.set()
        if self._worker:
            self._worker.join(timeout=1.5)

    def _loop(self) -> None:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=self.config.ambient_noise_adjust_seconds)
            while not self._stop.is_set():
                try:
                    audio = recognizer.listen(source, phrase_time_limit=self.config.phrase_time_limit_seconds)
                    text = recognizer.recognize_google(audio, language=self.config.language)
                    self.outbox.put(VoicePhrase(text=text, confidence=1.0))
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    continue
