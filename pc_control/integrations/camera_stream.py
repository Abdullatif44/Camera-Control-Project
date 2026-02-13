from __future__ import annotations

from dataclasses import dataclass
from threading import Event, Lock, Thread
from time import sleep
from typing import Optional

from pc_control.core.config import CameraConfig


@dataclass(slots=True)
class CameraFrame:
    image: object
    index: int


class CameraStream:
    def __init__(self, config: CameraConfig) -> None:
        self.config = config
        self._capture = None
        self._latest: Optional[CameraFrame] = None
        self._stop = Event()
        self._lock = Lock()
        self._worker: Thread | None = None

    def start(self) -> None:
        import cv2

        if self._worker and self._worker.is_alive():
            return

        self._capture = cv2.VideoCapture(self.config.device_index)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)

        self._stop.clear()
        self._worker = Thread(target=self._loop, daemon=True, name="camera-stream")
        self._worker.start()

    def stop(self) -> None:
        self._stop.set()
        if self._worker:
            self._worker.join(timeout=1.5)
        if self._capture:
            self._capture.release()
            self._capture = None

    def _loop(self) -> None:
        index = 0
        delay = 1.0 / max(self.config.target_fps, 1)
        while not self._stop.is_set() and self._capture is not None:
            ok, frame = self._capture.read()
            if not ok:
                sleep(delay)
                continue
            index += 1
            with self._lock:
                self._latest = CameraFrame(image=frame, index=index)
            sleep(delay / 2)

    def read_latest(self) -> Optional[CameraFrame]:
        with self._lock:
            return self._latest
