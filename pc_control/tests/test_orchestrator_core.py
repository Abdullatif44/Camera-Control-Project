from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from pc_control.core.config import AppConfig, VoiceConfig
from pc_control.core.models import Command
from pc_control.integrations.voice_engine import SpeechRecognitionListener, VoiceCommandMapper, VoicePhrase
from pc_control.services.event_bus import EventBus
from pc_control.services.orchestrator import AppOrchestrator


class VoiceMapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = VoiceCommandMapper()

    def test_maps_volume_up(self) -> None:
        command = self.mapper.to_command(VoicePhrase("please volume up now"))
        self.assertIsNotNone(command)
        assert command
        self.assertEqual(command.name, "system.volume.up")

    def test_maps_volume_down(self) -> None:
        command = self.mapper.to_command(VoicePhrase("volume down"))
        self.assertIsNotNone(command)
        assert command
        self.assertEqual(command.name, "system.volume.down")

    def test_maps_mute(self) -> None:
        command = self.mapper.to_command(VoicePhrase("mute"))
        self.assertIsNotNone(command)
        assert command
        self.assertEqual(command.name, "system.mute.toggle")

    def test_maps_click(self) -> None:
        command = self.mapper.to_command(VoicePhrase("do a left click"))
        self.assertIsNotNone(command)
        assert command
        self.assertEqual(command.name, "mouse.click.left")

    def test_maps_corner_move(self) -> None:
        command = self.mapper.to_command(VoicePhrase("move top right now"))
        self.assertIsNotNone(command)
        assert command
        self.assertEqual(command.name, "mouse.move.top_right")

    def test_maps_fast_scroll(self) -> None:
        command = self.mapper.to_command(VoicePhrase("scroll fast down"))
        self.assertIsNotNone(command)
        assert command
        self.assertEqual(command.name, "mouse.scroll.down")
        self.assertEqual(command.payload["scroll_delta"], -240)

    def test_unknown_returns_none(self) -> None:
        command = self.mapper.to_command(VoicePhrase("open the pod bay doors"))
        self.assertIsNone(command)


class VoiceListenerDependencyTests(unittest.TestCase):
    def test_start_fails_when_pyaudio_missing(self) -> None:
        listener = SpeechRecognitionListener(VoiceConfig())

        def fake_import(name: str):
            if name == "speech_recognition":
                return object()
            if name == "pyaudio":
                raise ModuleNotFoundError("No module named pyaudio")
            raise ModuleNotFoundError(name)

        with patch("importlib.import_module", side_effect=fake_import):
            started = listener.start()

        self.assertFalse(started)
        self.assertFalse(listener.available)
        self.assertIn("pyaudio", listener.unavailable_reason.lower())


class EventBusTests(unittest.TestCase):
    def test_subscribe_and_publish(self) -> None:
        from pc_control.core.models import DomainEvent, EventType

        bus = EventBus()
        received = []

        def handler(event):
            received.append(event.message)

        bus.subscribe(EventType.STARTUP, handler)
        bus.start()
        bus.publish(DomainEvent(EventType.STARTUP, "boot"))
        import time

        time.sleep(0.2)
        bus.stop()
        self.assertIn("boot", received)


class OrchestratorCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        cfg = AppConfig()
        cfg.auth.enabled = False
        cfg.voice.enabled = False
        self.app = AppOrchestrator(cfg, dry_run=True)
        self.app.state.is_running = True

    def tearDown(self) -> None:
        self.app.state.is_running = False

    def test_handle_allowed_command(self) -> None:
        self.app._handle_command(Command(name="mouse.click.left", source="test"))
        self.assertEqual(self.app.metrics.get().command_count, 1)

    def test_handle_blocked_command(self) -> None:
        self.app._handle_command(Command(name="invalid.command", source="test"))
        self.assertEqual(self.app.metrics.get().blocked_command_count, 1)

    def test_handle_executor_failure(self) -> None:
        self.app.executor.execute = Mock(side_effect=RuntimeError("boom"))
        self.app._handle_command(Command(name="mouse.click.left", source="test"))
        self.assertEqual(self.app.metrics.get().errors, 1)

    def test_commands_from_gesture_empty(self) -> None:
        class G:
            pointer = None
            click = False
            double_click = False
            right_click = False
            scroll_delta = 0

        out = self.app._commands_from_gesture(G())
        self.assertEqual(out, [])

    def test_commands_from_gesture_full(self) -> None:
        class P:
            x = 10
            y = 20

        class G:
            pointer = P()
            click = True
            double_click = True
            right_click = True
            scroll_delta = -120

        out = self.app._commands_from_gesture(G())
        names = [x.name for x in out]
        self.assertIn("mouse.move", names)
        self.assertIn("mouse.double_click", names)
        self.assertIn("mouse.click.right", names)
        self.assertIn("mouse.scroll.down", names)


if __name__ == "__main__":
    unittest.main()
