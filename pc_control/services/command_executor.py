from __future__ import annotations

from pc_control.core.models import Command
from pc_control.integrations.system_actions import MouseKeyboardAPI


class CommandExecutor:
    """Maps domain commands to platform actions."""

    def __init__(self, api: MouseKeyboardAPI) -> None:
        self.api = api

    def execute(self, command: Command) -> None:
        name = command.name
        payload = command.payload

        if name == "mouse.move":
            x = int(payload.get("screen_x", 0))
            y = int(payload.get("screen_y", 0))
            self.api.move_to(x, y)
            return

        if name == "mouse.move.center":
            self._move_to_anchor("center")
            return

        if name == "mouse.move.top_left":
            self._move_to_anchor("top_left")
            return

        if name == "mouse.move.top_right":
            self._move_to_anchor("top_right")
            return

        if name == "mouse.move.bottom_left":
            self._move_to_anchor("bottom_left")
            return

        if name == "mouse.move.bottom_right":
            self._move_to_anchor("bottom_right")
            return

        if name == "mouse.click.left":
            self.api.click_left()
            return

        if name == "mouse.click.right":
            self.api.click_right()
            return

        if name == "mouse.double_click":
            self.api.double_click()
            return

        if name == "mouse.scroll.up":
            self.api.scroll(int(payload.get("scroll_delta", 120)))
            return

        if name == "mouse.scroll.down":
            delta = int(payload.get("scroll_delta", -120))
            self.api.scroll(delta)
            return

        if name == "system.volume.up":
            self.api.key_press("volumeup")
            return

        if name == "system.volume.down":
            self.api.key_press("volumedown")
            return

        if name == "system.mute.toggle":
            self.api.key_press("volumemute")
            return

        if name == "system.lock":
            self.api.key_press("win")
            self.api.key_press("l")
            return

        raise ValueError(f"Unsupported command: {name}")

    def _move_to_anchor(self, anchor: str) -> None:
        import pyautogui

        width, height = pyautogui.size()
        margin = 40

        points = {
            "center": (width // 2, height // 2),
            "top_left": (margin, margin),
            "top_right": (max(width - margin, 0), margin),
            "bottom_left": (margin, max(height - margin, 0)),
            "bottom_right": (max(width - margin, 0), max(height - margin, 0)),
        }
        x, y = points[anchor]
        self.api.move_to(int(x), int(y))
