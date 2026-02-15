from __future__ import annotations

from dataclasses import dataclass
import importlib
from queue import Queue
from threading import Event, Thread
from typing import Optional

from pc_control.core.config import VoiceConfig
from pc_control.core.models import Command


@dataclass(slots=True)
class VoicePhrase:
    text: str
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class VoiceCommandSpec:
    command_name: str
    action_description: str
    payload: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class VoiceRule:
    examples: tuple[str, ...]
    spec: VoiceCommandSpec


class VoiceCommandMapper:
    def __init__(self) -> None:
        self.rules: tuple[VoiceRule, ...] = (
            VoiceRule(("volume up", "increase volume", "sound up", "louder"), VoiceCommandSpec("system.volume.up", "Increase system volume")),
            VoiceRule(("volume down", "decrease volume", "sound down", "lower volume", "quieter"), VoiceCommandSpec("system.volume.down", "Decrease system volume")),
            VoiceRule(("mute", "mute audio", "mute sound", "silence"), VoiceCommandSpec("system.mute.toggle", "Toggle mute/unmute")),
            VoiceRule(("left click", "single click", "click"), VoiceCommandSpec("mouse.click.left", "Left mouse click")),
            VoiceRule(("right click", "context click"), VoiceCommandSpec("mouse.click.right", "Right mouse click")),
            VoiceRule(("double click", "open item", "double tap"), VoiceCommandSpec("mouse.double_click", "Double left click")),
            VoiceRule(("scroll up", "page up", "go up"), VoiceCommandSpec("mouse.scroll.up", "Scroll upward", payload={"scroll_delta": 120})),
            VoiceRule(("scroll down", "page down", "go down"), VoiceCommandSpec("mouse.scroll.down", "Scroll downward", payload={"scroll_delta": -120})),
            VoiceRule(("scroll fast up", "scroll up fast", "big scroll up"), VoiceCommandSpec("mouse.scroll.up", "Scroll upward quickly", payload={"scroll_delta": 240})),
            VoiceRule(("scroll fast down", "scroll down fast", "big scroll down"), VoiceCommandSpec("mouse.scroll.down", "Scroll downward quickly", payload={"scroll_delta": -240})),
            VoiceRule(("lock computer", "lock pc", "lock system"), VoiceCommandSpec("system.lock", "Lock the computer")),
            VoiceRule(("move center", "cursor center", "mouse center"), VoiceCommandSpec("mouse.move.center", "Move cursor to screen center")),
            VoiceRule(("top left", "move top left", "cursor top left"), VoiceCommandSpec("mouse.move.top_left", "Move cursor to top-left corner")),
            VoiceRule(("top right", "move top right", "cursor top right"), VoiceCommandSpec("mouse.move.top_right", "Move cursor to top-right corner")),
            VoiceRule(("bottom left", "move bottom left", "cursor bottom left"), VoiceCommandSpec("mouse.move.bottom_left", "Move cursor to bottom-left corner")),
            VoiceRule(("bottom right", "move bottom right", "cursor bottom right"), VoiceCommandSpec("mouse.move.bottom_right", "Move cursor to bottom-right corner")),
        )

    def reference(self) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        for rule in self.rules:
            phrase = rule.examples[0]
            rows.append((phrase, rule.spec.command_name, rule.spec.action_description))
        return rows

    def to_command(self, phrase: VoicePhrase) -> Optional[Command]:
        normalized = phrase.text.strip().lower()
        for rule in self.rules:
            if any(example in normalized for example in rule.examples):
                payload = dict(rule.spec.payload or {})
                return Command(name=rule.spec.command_name, source="voice", payload=payload)
        return None


class SpeechRecognitionListener:
    def __init__(self, config: VoiceConfig) -> None:
        self.config = config
        self.outbox: Queue[VoicePhrase] = Queue()
        self._stop = Event()
        self._worker: Thread | None = None

        self.available: bool = config.enabled
        self.unavailable_reason: str = ""
        self._sr = None

    def start(self) -> bool:
        if self._worker and self._worker.is_alive():
            return True
        if not self.config.enabled:
            self.available = False
            self.unavailable_reason = "Voice recognition disabled by configuration."
            return False

        if not self._ensure_dependencies():
            return False

        self._stop.clear()
        self._worker = Thread(target=self._loop, daemon=True, name="voice-listener")
        self._worker.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._worker:
            self._worker.join(timeout=1.5)

    def _ensure_dependencies(self) -> bool:
        try:
            self._sr = importlib.import_module("speech_recognition")
        except Exception as exc:
            self.available = False
            self.unavailable_reason = f"Missing dependency 'speech_recognition': {exc}"
            return False

        try:
            importlib.import_module("pyaudio")
        except Exception as exc:
            self.available = False
            self.unavailable_reason = (
                f"Missing dependency 'pyaudio': {exc}. Install it to enable microphone voice commands."
            )
            return False

        self.available = True
        self.unavailable_reason = ""
        return True

    def _loop(self) -> None:
        assert self._sr is not None
        sr = self._sr
        recognizer = sr.Recognizer()

        try:
            mic = sr.Microphone()
        except Exception as exc:
            self.available = False
            self.unavailable_reason = f"Microphone initialization failed: {exc}"
            return

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
                except Exception as exc:
                    self.available = False
                    self.unavailable_reason = f"Voice listener stopped due to runtime error: {exc}"
                    return
