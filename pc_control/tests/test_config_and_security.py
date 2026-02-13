from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from pc_control.core.config import AppConfig, load_first_available_config
from pc_control.core.models import Command
from pc_control.services.security import CommandGuard


class AppConfigTests(unittest.TestCase):
    def test_default_load_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "missing.json"
            config = AppConfig.from_file(missing)
            self.assertEqual(config.environment, "dev")
            self.assertTrue(config.voice.enabled)

    def test_load_from_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "app.json"
            payload = {
                "environment": "prod",
                "camera": {"width": 1920, "height": 1080},
                "voice": {"enabled": False},
            }
            file.write_text(json.dumps(payload), encoding="utf-8")
            config = AppConfig.from_file(file)
            self.assertEqual(config.environment, "prod")
            self.assertEqual(config.camera.width, 1920)
            self.assertFalse(config.voice.enabled)

    def test_load_first_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            p1 = Path(temp) / "a.json"
            p2 = Path(temp) / "b.json"
            p2.write_text(json.dumps({"environment": "stage"}), encoding="utf-8")
            config = load_first_available_config([p1, p2])
            self.assertEqual(config.environment, "stage")


class SecurityGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = CommandGuard(AppConfig().security)

    def test_allows_known_command(self) -> None:
        command = Command(name="mouse.click.left", source="test")
        result = self.guard.validate(command)
        self.assertTrue(result.accepted)

    def test_blocks_unknown_command(self) -> None:
        command = Command(name="nuke.everything", source="test")
        result = self.guard.validate(command)
        self.assertFalse(result.accepted)

    def test_rejects_bad_coordinate_type(self) -> None:
        command = Command(name="mouse.move", source="test", payload={"screen_x": "x", "screen_y": 1})
        result = self.guard.validate(command)
        self.assertFalse(result.accepted)

    def test_rejects_scroll_bounds(self) -> None:
        command = Command(name="mouse.scroll.up", source="test", payload={"scroll_delta": 999})
        result = self.guard.validate(command)
        self.assertFalse(result.accepted)

    def test_rejects_empty_name(self) -> None:
        command = Command(name="", source="test")
        result = self.guard.validate(command)
        self.assertFalse(result.accepted)


if __name__ == "__main__":
    unittest.main()
