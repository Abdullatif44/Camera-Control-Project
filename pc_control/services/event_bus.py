from __future__ import annotations

from collections import defaultdict
from queue import Empty, Queue
from threading import Event, Thread
from typing import Callable, DefaultDict, Dict, List

from pc_control.core.models import DomainEvent, EventType


EventHandler = Callable[[DomainEvent], None]


class EventBus:
    """Thread-safe in-process event bus for domain events."""

    def __init__(self) -> None:
        self._handlers: DefaultDict[EventType, List[EventHandler]] = defaultdict(list)
        self._any_handlers: List[EventHandler] = []
        self._queue: Queue[DomainEvent] = Queue()
        self._stop = Event()
        self._worker: Thread | None = None

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    def subscribe_any(self, handler: EventHandler) -> None:
        self._any_handlers.append(handler)

    def publish(self, event: DomainEvent) -> None:
        self._queue.put(event)

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop.clear()
        self._worker = Thread(target=self._loop, daemon=True, name="event-bus")
        self._worker.start()

    def stop(self) -> None:
        self._stop.set()
        if self._worker:
            self._worker.join(timeout=1.5)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                event = self._queue.get(timeout=0.2)
            except Empty:
                continue

            for handler in self._handlers.get(event.event_type, []):
                handler(event)

            for handler in self._any_handlers:
                handler(event)

    def stats(self) -> Dict[str, int]:
        return {
            "registered_typed_handlers": sum(len(v) for v in self._handlers.values()),
            "registered_any_handlers": len(self._any_handlers),
            "queued_events": self._queue.qsize(),
        }
