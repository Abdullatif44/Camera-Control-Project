from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import List, Optional, Tuple

from pc_control.core.config import GestureConfig
from pc_control.core.models import GestureFrame, Point


@dataclass(slots=True)
class Landmark:
    x: float
    y: float
    z: float = 0.0


@dataclass(slots=True)
class HandLandmarks:
    thumb_tip: Landmark
    index_tip: Landmark
    index_pip: Landmark
    middle_tip: Landmark
    middle_pip: Landmark
    ring_tip: Landmark
    ring_pip: Landmark
    pinky_tip: Landmark
    pinky_pip: Landmark
    wrist: Landmark


class PointerSmoother:
    def __init__(self, alpha: float, deadzone_px: int) -> None:
        self.alpha = alpha
        self.deadzone_px = deadzone_px
        self.last_x: float | None = None
        self.last_y: float | None = None

    def apply(self, x: float, y: float) -> tuple[int, int]:
        if self.last_x is None or self.last_y is None:
            self.last_x, self.last_y = x, y
            return int(x), int(y)

        dx = x - self.last_x
        dy = y - self.last_y
        if abs(dx) <= self.deadzone_px:
            dx = 0.0
        if abs(dy) <= self.deadzone_px:
            dy = 0.0

        self.last_x = self.last_x + dx * self.alpha
        self.last_y = self.last_y + dy * self.alpha
        return int(self.last_x), int(self.last_y)


class GestureInterpreter:
    """Pure-python gesture interpretation for predictable testing."""

    def __init__(self, config: GestureConfig) -> None:
        self.config = config
        self.smoother = PointerSmoother(config.smoothing_alpha, config.deadzone_px)
        self.last_click_ts = 0.0
        self.last_right_click_ts = 0.0
        self.drag_start_ts: float | None = None

    @staticmethod
    def _distance(a: Landmark, b: Landmark) -> float:
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5

    def _is_folded(self, tip: Landmark, pip: Landmark) -> bool:
        return tip.y > pip.y

    def _is_fist(self, hand: HandLandmarks) -> bool:
        folded = 0
        if self._is_folded(hand.index_tip, hand.index_pip):
            folded += 1
        if self._is_folded(hand.middle_tip, hand.middle_pip):
            folded += 1
        if self._is_folded(hand.ring_tip, hand.ring_pip):
            folded += 1
        if self._is_folded(hand.pinky_tip, hand.pinky_pip):
            folded += 1
        return folded >= 3

    def _map_pointer(self, hand: HandLandmarks, screen_size: tuple[int, int], mirrored: bool) -> tuple[int, int]:
        screen_w, screen_h = screen_size
        x = hand.index_tip.x * screen_w
        y = hand.index_tip.y * screen_h
        if mirrored:
            x = screen_w - x
        return self.smoother.apply(x, y)

    def process(self, hand: Optional[HandLandmarks], screen_size: tuple[int, int], mirrored: bool = True) -> GestureFrame:
        if hand is None:
            self.drag_start_ts = None
            return GestureFrame(hand_present=False)

        px, py = self._map_pointer(hand, screen_size, mirrored)
        frame = GestureFrame(
            pointer=Point(px, py),
            confidence=1.0,
            hand_present=True,
        )

        click_distance = self._distance(hand.index_tip, hand.thumb_tip)
        right_click_distance = self._distance(hand.middle_tip, hand.thumb_tip)

        now = monotonic()
        if click_distance < self.config.click_distance_threshold:
            if now - self.last_click_ts > 0.15:
                frame.click = True
                if now - self.last_click_ts < self.config.double_click_cooldown_seconds:
                    frame.double_click = True
                self.last_click_ts = now

        if right_click_distance < self.config.right_click_distance_threshold:
            if now - self.last_right_click_ts > 0.5:
                frame.right_click = True
                self.last_right_click_ts = now

        if self._is_fist(hand):
            if self.drag_start_ts is None:
                self.drag_start_ts = now
            frame.drag = (now - self.drag_start_ts) >= self.config.drag_hold_threshold_seconds
        else:
            self.drag_start_ts = None

        vertical = hand.index_tip.y - hand.wrist.y
        if vertical < -0.35:
            frame.scroll_delta = 120
        elif vertical > 0.35:
            frame.scroll_delta = -120

        frame.raw = {
            "click_distance": click_distance,
            "right_click_distance": right_click_distance,
            "fist": self._is_fist(hand),
            "vertical": vertical,
        }
        return frame


class MediaPipeHandAdapter:
    """Adapter using MediaPipe Tasks API (0.10+)"""

    def __init__(self, max_hands: int, min_detection: float, min_tracking: float) -> None:
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        self.mp = mp

        base_options = python.BaseOptions(
            model_asset_path="models/hand_landmarker.task"
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_hands
        )

        self.detector = vision.HandLandmarker.create_from_options(options)

    def parse(self, frame_bgr):
        import cv2

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        mp_image = self.mp.Image(
            image_format=self.mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.detector.detect(mp_image)

        if not result.hand_landmarks:
            return []

        parsed = []

        for hand in result.hand_landmarks:
            parsed.append(
                HandLandmarks(
                    thumb_tip=self._to(hand[4]),
                    index_tip=self._to(hand[8]),
                    index_pip=self._to(hand[6]),
                    middle_tip=self._to(hand[12]),
                    middle_pip=self._to(hand[10]),
                    ring_tip=self._to(hand[16]),
                    ring_pip=self._to(hand[14]),
                    pinky_tip=self._to(hand[20]),
                    pinky_pip=self._to(hand[18]),
                    wrist=self._to(hand[0]),
                )
            )

        return parsed

    @staticmethod
    def _to(lm):
        return Landmark(x=float(lm.x), y=float(lm.y), z=float(lm.z))
