from __future__ import annotations

import unittest

from pc_control.core.config import GestureConfig
from pc_control.core.models import Command
from pc_control.integrations.gesture_engine import GestureInterpreter, HandLandmarks, Landmark
from pc_control.integrations.system_actions import DryRunAdapter
from pc_control.services.command_executor import CommandExecutor


def hand_factory(
    index=(0.5, 0.5),
    thumb=(0.4, 0.5),
    middle=(0.6, 0.5),
    ring=(0.65, 0.52),
    pinky=(0.7, 0.52),
    wrist=(0.5, 0.75),
):
    return HandLandmarks(
        thumb_tip=Landmark(*thumb),
        index_tip=Landmark(*index),
        index_pip=Landmark(index[0], index[1] - 0.1),
        middle_tip=Landmark(*middle),
        middle_pip=Landmark(middle[0], middle[1] - 0.1),
        ring_tip=Landmark(*ring),
        ring_pip=Landmark(ring[0], ring[1] - 0.1),
        pinky_tip=Landmark(*pinky),
        pinky_pip=Landmark(pinky[0], pinky[1] - 0.1),
        wrist=Landmark(*wrist),
    )


class GestureInterpreterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.interpreter = GestureInterpreter(GestureConfig())

    def test_no_hand_returns_absent(self) -> None:
        frame = self.interpreter.process(None, (1920, 1080), mirrored=True)
        self.assertFalse(frame.hand_present)
        self.assertIsNone(frame.pointer)

    def test_pointer_is_mapped(self) -> None:
        hand = hand_factory(index=(0.25, 0.4))
        frame = self.interpreter.process(hand, (1000, 1000), mirrored=False)
        self.assertTrue(frame.hand_present)
        self.assertIsNotNone(frame.pointer)
        assert frame.pointer
        self.assertGreaterEqual(frame.pointer.x, 200)

    def test_click_detected(self) -> None:
        hand = hand_factory(index=(0.50, 0.50), thumb=(0.505, 0.505))
        frame = self.interpreter.process(hand, (1000, 1000), mirrored=False)
        self.assertTrue(frame.click)

    def test_right_click_detected(self) -> None:
        hand = hand_factory(middle=(0.50, 0.50), thumb=(0.505, 0.505))
        frame = self.interpreter.process(hand, (1000, 1000), mirrored=False)
        self.assertTrue(frame.right_click)

    def test_scroll_up_detected(self) -> None:
        hand = hand_factory(index=(0.5, 0.2), wrist=(0.5, 0.8))
        frame = self.interpreter.process(hand, (1000, 1000), mirrored=False)
        self.assertEqual(frame.scroll_delta, 120)

    def test_scroll_down_detected(self) -> None:
        hand = hand_factory(index=(0.5, 0.95), wrist=(0.5, 0.4))
        frame = self.interpreter.process(hand, (1000, 1000), mirrored=False)
        self.assertEqual(frame.scroll_delta, -120)


class ExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = DryRunAdapter()
        self.executor = CommandExecutor(self.api)

    def test_move(self) -> None:
        self.executor.execute(Command(name="mouse.move", source="test", payload={"screen_x": 10, "screen_y": 20}))
        self.assertIn("move:10,20", self.api.actions)

    def test_move_anchor_commands(self) -> None:
        class FakePyAutoGUI:
            @staticmethod
            def size():
                return (1000, 800)

        original = __import__("sys").modules.get("pyautogui")
        __import__("sys").modules["pyautogui"] = FakePyAutoGUI
        try:
            self.executor.execute(Command(name="mouse.move.center", source="test"))
            self.executor.execute(Command(name="mouse.move.top_left", source="test"))
            self.executor.execute(Command(name="mouse.move.bottom_right", source="test"))
        finally:
            if original is not None:
                __import__("sys").modules["pyautogui"] = original
            else:
                del __import__("sys").modules["pyautogui"]

        self.assertIn("move:500,400", self.api.actions)
        self.assertIn("move:40,40", self.api.actions)
        self.assertIn("move:960,760", self.api.actions)

    def test_clicks(self) -> None:
        self.executor.execute(Command(name="mouse.click.left", source="test"))
        self.executor.execute(Command(name="mouse.click.right", source="test"))
        self.executor.execute(Command(name="mouse.double_click", source="test"))
        self.assertIn("click:left", self.api.actions)
        self.assertIn("click:right", self.api.actions)
        self.assertIn("click:double", self.api.actions)

    def test_scroll(self) -> None:
        self.executor.execute(Command(name="mouse.scroll.up", source="test", payload={"scroll_delta": 80}))
        self.executor.execute(Command(name="mouse.scroll.down", source="test", payload={"scroll_delta": -80}))
        self.assertIn("scroll:80", self.api.actions)
        self.assertIn("scroll:-80", self.api.actions)

    def test_volume(self) -> None:
        self.executor.execute(Command(name="system.volume.up", source="test"))
        self.executor.execute(Command(name="system.volume.down", source="test"))
        self.executor.execute(Command(name="system.mute.toggle", source="test"))
        self.assertIn("key:volumeup", self.api.actions)
        self.assertIn("key:volumedown", self.api.actions)
        self.assertIn("key:volumemute", self.api.actions)

    def test_lock(self) -> None:
        self.executor.execute(Command(name="system.lock", source="test"))
        self.assertIn("key:win", self.api.actions)
        self.assertIn("key:l", self.api.actions)

    def test_unsupported_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.executor.execute(Command(name="unknown", source="test"))


if __name__ == "__main__":
    unittest.main()
