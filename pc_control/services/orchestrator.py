from __future__ import annotations

from queue import Empty
from threading import Event, Thread
from time import monotonic, sleep

from pc_control.core.config import AppConfig
from pc_control.core.logging_utils import get_logger
from pc_control.core.models import Command, DomainEvent, EventType, RuntimeState
from pc_control.integrations.auth_engine import FaceAuthenticator
from pc_control.integrations.camera_stream import CameraStream
from pc_control.integrations.gesture_engine import GestureInterpreter, MediaPipeHandAdapter
from pc_control.integrations.system_actions import DryRunAdapter, PyAutoGuiAdapter
from pc_control.integrations.voice_engine import SpeechRecognitionListener, VoiceCommandMapper
from pc_control.services.command_executor import CommandExecutor
from pc_control.services.event_bus import EventBus
from pc_control.services.metrics import MetricsCollector, MetricsWriter
from pc_control.services.security import CommandGuard


class AppOrchestrator:
    def __init__(self, config: AppConfig, dry_run: bool = False) -> None:
        self.config = config
        self.log = get_logger("pc_control.orchestrator")

        self.state = RuntimeState()
        self.events = EventBus()
        self.metrics = MetricsCollector()
        self.metrics_writer = MetricsWriter(
            self.metrics,
            output_path=config.metrics.output_path,
            interval_seconds=config.metrics.write_interval_seconds,
        )

        self.guard = CommandGuard(config.security)
        self.api = DryRunAdapter() if dry_run else PyAutoGuiAdapter()
        self.executor = CommandExecutor(self.api)

        self.authenticator = FaceAuthenticator(config.auth)
        self.camera = CameraStream(config.camera)
        self.gesture_engine = GestureInterpreter(config.gesture)
        self.hand_adapter = None

        self.voice_listener = SpeechRecognitionListener(config.voice)
        self.voice_mapper = VoiceCommandMapper()

        self._stop = Event()
        self._workers: list[Thread] = []
        self._started_at = 0.0

        self.events.subscribe_any(self._log_events)

    def start(self) -> None:
        if self.state.is_running:
            return

        self._started_at = monotonic()
        self.state.is_running = True
        self._stop.clear()
        self.events.start()

        self.metrics_writer.start()
        self.events.publish(DomainEvent(EventType.STARTUP, "Application startup."))

        if not self._authenticate_phase():
            self.stop()
            return

        self.hand_adapter = MediaPipeHandAdapter(
            max_hands=self.config.gesture.hand_max_num,
            min_detection=self.config.gesture.min_detection_confidence,
            min_tracking=self.config.gesture.min_tracking_confidence,
        )

        self.camera.start()
        self.voice_listener.start()

        workers = [
            Thread(target=self._gesture_loop, daemon=True, name="gesture-loop"),
            Thread(target=self._voice_loop, daemon=True, name="voice-loop"),
            Thread(target=self._heartbeat_loop, daemon=True, name="heartbeat-loop"),
        ]
        self._workers = workers
        for worker in workers:
            worker.start()

    def stop(self) -> None:
        if not self.state.is_running:
            return

        self._stop.set()
        for worker in self._workers:
            worker.join(timeout=2.0)
        self._workers.clear()

        self.voice_listener.stop()
        self.camera.stop()

        self.state.is_running = False
        self.state.uptime_seconds = max(monotonic() - self._started_at, 0.0)

        self.events.publish(
            DomainEvent(
                EventType.SHUTDOWN,
                "Application shutdown.",
                context={"uptime": self.state.uptime_seconds},
            )
        )
        self.metrics_writer.write_now()
        self.metrics_writer.stop()
        self.events.stop()

    def _authenticate_phase(self) -> bool:
        if not self.config.auth.enabled:
            self.state.is_authenticated = True
            self.events.publish(DomainEvent(EventType.AUTH_SUCCESS, "Auth disabled; bypassed."))
            return True

        self.metrics.incr("auth_attempts", 1)
        try:
            result = self.authenticator.authenticate()
        except Exception as exc:
            self.metrics.incr("errors", 1)
            self.state.mark_error(str(exc))
            self.events.publish(
                DomainEvent(EventType.ERROR, "Authentication exception.", context={"error": str(exc)})
            )
            return False

        if result.success:
            self.state.is_authenticated = True
            self.metrics.incr("auth_successes", 1)
            self.events.publish(
                DomainEvent(EventType.AUTH_SUCCESS, "Authentication successful.", context={"attempts": result.attempts})
            )
            return True

        self.events.publish(
            DomainEvent(
                EventType.AUTH_FAILURE,
                "Authentication failed.",
                context={"attempts": result.attempts, "reason": result.reason},
            )
        )
        return False

    def _gesture_loop(self) -> None:
        import pyautogui

        screen = pyautogui.size()

        while not self._stop.is_set():
            frame = self.camera.read_latest()
            if frame is None:
                sleep(0.01)
                continue

            if self.hand_adapter is None:
                sleep(0.01)
                continue
            hands = self.hand_adapter.parse(frame.image)
            hand = hands[0] if hands else None
            gesture = self.gesture_engine.process(hand, screen, mirrored=self.config.camera.mirrored)

            self.metrics.incr("gesture_frames_processed", 1)
            self.events.publish(
                DomainEvent(
                    EventType.GESTURE_FRAME,
                    "Processed gesture frame.",
                    context={"hand_present": gesture.hand_present, "index": frame.index},
                )
            )

            generated = self._commands_from_gesture(gesture)
            for command in generated:
                self._handle_command(command)

            sleep(0.01)

    def _commands_from_gesture(self, gesture) -> list[Command]:
        commands: list[Command] = []
        if gesture.pointer is not None:
            commands.append(
                Command(
                    name="mouse.move",
                    source="gesture",
                    payload={"screen_x": int(gesture.pointer.x), "screen_y": int(gesture.pointer.y)},
                )
            )

        if gesture.click:
            if gesture.double_click:
                commands.append(Command(name="mouse.double_click", source="gesture"))
            else:
                commands.append(Command(name="mouse.click.left", source="gesture"))

        if gesture.right_click:
            commands.append(Command(name="mouse.click.right", source="gesture"))

        if gesture.scroll_delta > 0:
            commands.append(
                Command(name="mouse.scroll.up", source="gesture", payload={"scroll_delta": gesture.scroll_delta})
            )

        if gesture.scroll_delta < 0:
            commands.append(
                Command(name="mouse.scroll.down", source="gesture", payload={"scroll_delta": gesture.scroll_delta})
            )

        return commands

    def _voice_loop(self) -> None:
        while not self._stop.is_set():
            try:
                phrase = self.voice_listener.outbox.get(timeout=0.2)
            except Empty:
                continue
            self.metrics.incr("voice_commands_heard", 1)
            command = self.voice_mapper.to_command(phrase)
            if command is None:
                self.events.publish(
                    DomainEvent(
                        EventType.WARNING,
                        "Unmapped voice command ignored.",
                        context={"text": phrase.text},
                    )
                )
                self.metrics.incr("warnings", 1)
                continue
            self.events.publish(
                DomainEvent(
                    EventType.VOICE_COMMAND,
                    "Voice command recognized.",
                    context={"command": command.name, "text": phrase.text},
                )
            )
            self._handle_command(command)

    def _heartbeat_loop(self) -> None:
        while not self._stop.is_set():
            self.state.uptime_seconds = max(monotonic() - self._started_at, 0.0)
            self.events.publish(
                DomainEvent(
                    EventType.HEARTBEAT,
                    "App heartbeat.",
                    context={
                        "uptime_seconds": round(self.state.uptime_seconds, 1),
                        "metrics": self.metrics.get().to_dict(),
                    },
                )
            )
            sleep(5.0)

    def _handle_command(self, command: Command) -> None:
        validated = self.guard.validate(command)
        if not validated.accepted:
            self.metrics.incr("blocked_command_count", 1)
            self.events.publish(
                DomainEvent(
                    EventType.COMMAND_BLOCKED,
                    "Command blocked by security policy.",
                    context={"command": command.name, "reason": validated.reason},
                )
            )
            return

        try:
            self.executor.execute(command)
            self.metrics.incr("command_count", 1)
            self.events.publish(
                DomainEvent(
                    EventType.COMMAND_EXECUTED,
                    "Command executed.",
                    context={"command": command.name, "source": command.source},
                )
            )
        except Exception as exc:
            self.metrics.incr("errors", 1)
            self.state.mark_error(str(exc))
            self.events.publish(
                DomainEvent(
                    EventType.ERROR,
                    "Command execution failed.",
                    context={"command": command.name, "error": str(exc)},
                )
            )

    def _log_events(self, event: DomainEvent) -> None:
        if event.event_type in {EventType.ERROR, EventType.AUTH_FAILURE}:
            self.log.error("%s | %s | %s", event.event_type, event.message, event.context)
            return
        if event.event_type in {EventType.WARNING, EventType.COMMAND_BLOCKED}:
            self.log.warning("%s | %s | %s", event.event_type, event.message, event.context)
            return
        self.log.info("%s | %s", event.event_type, event.message)
