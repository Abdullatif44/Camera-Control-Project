from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from threading import Event, Lock, Thread
import json
import time

from pc_control.core.models import MetricsSnapshot


class MetricsCollector:
    def __init__(self) -> None:
        self._snapshot = MetricsSnapshot()
        self._lock = Lock()

    def incr(self, field_name: str, value: int = 1) -> None:
        with self._lock:
            current = getattr(self._snapshot, field_name)
            setattr(self._snapshot, field_name, current + value)

    def get(self) -> MetricsSnapshot:
        with self._lock:
            return MetricsSnapshot(**asdict(self._snapshot))


class MetricsWriter:
    def __init__(self, collector: MetricsCollector, output_path: str, interval_seconds: float) -> None:
        self.collector = collector
        self.output_path = Path(output_path)
        self.interval_seconds = interval_seconds
        self._stop = Event()
        self._worker: Thread | None = None

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._stop.clear()
        self._worker = Thread(target=self._loop, daemon=True, name="metrics-writer")
        self._worker.start()

    def stop(self) -> None:
        self._stop.set()
        if self._worker:
            self._worker.join(timeout=1.2)

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.write_now()
            time.sleep(self.interval_seconds)

    def write_now(self) -> None:
        snapshot = self.collector.get().to_dict()
        payload = {
            "timestamp": time.time(),
            "snapshot": snapshot,
        }
        self.output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
