from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List
import json


@dataclass(slots=True)
class CameraConfig:
    device_index: int = 0
    width: int = 1280
    height: int = 720
    target_fps: int = 30
    mirrored: bool = True


@dataclass(slots=True)
class GestureConfig:
    hand_max_num: int = 1
    min_detection_confidence: float = 0.70
    min_tracking_confidence: float = 0.50
    click_distance_threshold: float = 0.045
    right_click_distance_threshold: float = 0.050
    double_click_cooldown_seconds: float = 0.8
    drag_hold_threshold_seconds: float = 0.6
    smoothing_alpha: float = 0.25
    deadzone_px: int = 4


@dataclass(slots=True)
class VoiceConfig:
    enabled: bool = True
    phrase_time_limit_seconds: float = 4.0
    ambient_noise_adjust_seconds: float = 1.0
    language: str = "en-US"
    command_timeout_seconds: float = 5.0


@dataclass(slots=True)
class AuthenticationConfig:
    enabled: bool = True
    face_image_path: str = "user.png"
    acceptance_tolerance: float = 0.45
    max_attempts: int = 2


@dataclass(slots=True)
class SecurityConfig:
    fail_closed: bool = True
    redact_sensitive_logs: bool = True
    allowed_commands: List[str] = field(
        default_factory=lambda: [
            "mouse.move",
            "mouse.click.left",
            "mouse.click.right",
            "mouse.double_click",
            "mouse.scroll.up",
            "mouse.scroll.down",
            "system.volume.up",
            "system.volume.down",
            "system.mute.toggle",
            "system.lock",
        ]
    )


@dataclass(slots=True)
class MetricsConfig:
    enabled: bool = True
    write_interval_seconds: float = 10.0
    output_path: str = "runtime/metrics.json"


@dataclass(slots=True)
class LoggingConfig:
    level: str = "INFO"
    path: str = "runtime/pc_control.log"
    rotation_megabytes: int = 5
    backup_count: int = 5


@dataclass(slots=True)
class AppConfig:
    environment: str = "dev"
    camera: CameraConfig = field(default_factory=CameraConfig)
    gesture: GestureConfig = field(default_factory=GestureConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    auth: AuthenticationConfig = field(default_factory=AuthenticationConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @staticmethod
    def from_dict(payload: Dict[str, object]) -> "AppConfig":
        camera = CameraConfig(**payload.get("camera", {}))
        gesture = GestureConfig(**payload.get("gesture", {}))
        voice = VoiceConfig(**payload.get("voice", {}))
        auth = AuthenticationConfig(**payload.get("auth", {}))
        security = SecurityConfig(**payload.get("security", {}))
        metrics = MetricsConfig(**payload.get("metrics", {}))
        logging = LoggingConfig(**payload.get("logging", {}))
        return AppConfig(
            environment=str(payload.get("environment", "dev")),
            camera=camera,
            gesture=gesture,
            voice=voice,
            auth=auth,
            security=security,
            metrics=metrics,
            logging=logging,
        )

    @staticmethod
    def from_file(path: str | Path) -> "AppConfig":
        config_path = Path(path)
        if not config_path.exists():
            return AppConfig()
        content = config_path.read_text(encoding="utf-8")
        payload = json.loads(content)
        return AppConfig.from_dict(payload)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)



DEFAULT_CONFIG_PATHS = [
    Path("config/app.json"),
    Path("config/app.local.json"),
    Path("app.json"),
]


def load_first_available_config(paths: List[Path] | None = None) -> AppConfig:
    for path in (paths or DEFAULT_CONFIG_PATHS):
        if path.exists():
            return AppConfig.from_file(path)
    return AppConfig()
