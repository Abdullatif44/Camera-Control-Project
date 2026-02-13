from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from pc_control.core.config import SecurityConfig
from pc_control.core.models import Command


@dataclass(slots=True)
class ValidationResult:
    accepted: bool
    reason: str = ""


class CommandGuard:
    def __init__(self, config: SecurityConfig) -> None:
        self._allowed = set(config.allowed_commands)
        self._fail_closed = config.fail_closed

    def validate(self, command: Command) -> ValidationResult:
        if not command.name:
            return ValidationResult(accepted=False, reason="Empty command name.")

        if command.name not in self._allowed:
            return ValidationResult(
                accepted=not self._fail_closed,
                reason=f"Command '{command.name}' not in allow-list.",
            )

        payload_ok, reason = self._validate_payload(command.payload)
        return ValidationResult(accepted=payload_ok, reason=reason)

    def _validate_payload(self, payload: Dict[str, object]) -> tuple[bool, str]:
        for key, value in payload.items():
            if key.endswith("_x") or key.endswith("_y"):
                if not isinstance(value, (int, float)):
                    return False, f"Coordinate '{key}' must be numeric."
            if key == "scroll_delta":
                if not isinstance(value, int):
                    return False, "scroll_delta must be integer."
                if abs(value) > 300:
                    return False, "scroll_delta out of accepted bounds."
        return True, ""
