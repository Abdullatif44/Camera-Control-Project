from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time


class EventType(str, Enum):
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    HEARTBEAT = "heartbeat"
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    GESTURE_FRAME = "gesture.frame"
    GESTURE_COMMAND = "gesture.command"
    VOICE_COMMAND = "voice.command"
    COMMAND_EXECUTED = "command.executed"
    COMMAND_BLOCKED = "command.blocked"
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True)
class Point:
    x: float
    y: float


@dataclass(slots=True)
class GestureFrame:
    pointer: Optional[Point] = None
    confidence: float = 0.0
    hand_present: bool = False
    click: bool = False
    right_click: bool = False
    double_click: bool = False
    scroll_delta: int = 0
    drag: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Command:
    name: str
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def with_payload(self, **kwargs: Any) -> "Command":
        merged = dict(self.payload)
        merged.update(kwargs)
        return Command(name=self.name, source=self.source, payload=merged)


@dataclass(slots=True)
class DomainEvent:
    event_type: EventType
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass(slots=True)
class RuntimeState:
    is_running: bool = False
    is_authenticated: bool = False
    active_profile: str = "default"
    uptime_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)

    def mark_error(self, error: str) -> None:
        self.errors.append(error)


@dataclass(slots=True)
class MetricsSnapshot:
    command_count: int = 0
    blocked_command_count: int = 0
    gesture_frames_processed: int = 0
    auth_attempts: int = 0
    auth_successes: int = 0
    voice_commands_heard: int = 0
    warnings: int = 0
    errors: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "command_count": self.command_count,
            "blocked_command_count": self.blocked_command_count,
            "gesture_frames_processed": self.gesture_frames_processed,
            "auth_attempts": self.auth_attempts,
            "auth_successes": self.auth_successes,
            "voice_commands_heard": self.voice_commands_heard,
            "warnings": self.warnings,
            "errors": self.errors,
        }
