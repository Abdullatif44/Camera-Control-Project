from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class MouseKeyboardAPI(Protocol):
    def move_to(self, x: int, y: int) -> None:
        ...

    def click_left(self) -> None:
        ...

    def click_right(self) -> None:
        ...

    def double_click(self) -> None:
        ...

    def scroll(self, delta: int) -> None:
        ...

    def key_press(self, key_name: str) -> None:
        ...


@dataclass(slots=True)
class PyAutoGuiAdapter:
    """Concrete adapter to isolate pyautogui from business logic."""

    def move_to(self, x: int, y: int) -> None:
        import pyautogui

        pyautogui.moveTo(x, y)

    def click_left(self) -> None:
        import pyautogui

        pyautogui.click()

    def click_right(self) -> None:
        import pyautogui

        pyautogui.click(button="right")

    def double_click(self) -> None:
        import pyautogui

        pyautogui.doubleClick()

    def scroll(self, delta: int) -> None:
        import pyautogui

        pyautogui.scroll(delta)

    def key_press(self, key_name: str) -> None:
        import pyautogui

        pyautogui.press(key_name)


class DryRunAdapter:
    """Used for local testing and CI where hardware actions are undesirable."""

    def __init__(self) -> None:
        self.actions: list[str] = []

    def move_to(self, x: int, y: int) -> None:
        self.actions.append(f"move:{x},{y}")

    def click_left(self) -> None:
        self.actions.append("click:left")

    def click_right(self) -> None:
        self.actions.append("click:right")

    def double_click(self) -> None:
        self.actions.append("click:double")

    def scroll(self, delta: int) -> None:
        self.actions.append(f"scroll:{delta}")

    def key_press(self, key_name: str) -> None:
        self.actions.append(f"key:{key_name}")
