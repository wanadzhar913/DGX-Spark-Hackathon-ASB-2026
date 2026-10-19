"""
In-memory event store + WebSocket broadcasting (Task 6).

- `EventStore` keeps a bounded ring buffer of recent events in RAM (resets on
  restart) and lets the API fetch an event's snapshot bytes by id.
- `EventBroadcaster` pushes each new event's public JSON to all connected
  WebSocket clients.
"""

from __future__ import annotations

import asyncio
import threading
from collections import OrderedDict
from typing import Dict, List, Optional

from .models import Event


class EventStore:
    def __init__(self, capacity: int = 500):
        self.capacity = capacity
        self._events: "OrderedDict[str, Event]" = OrderedDict()
        self._lock = threading.Lock()

    def add(self, event: Event) -> None:
        with self._lock:
            self._events[event.id] = event
            while len(self._events) > self.capacity:
                self._events.popitem(last=False)  # drop oldest

    def get(self, event_id: str) -> Optional[Event]:
        with self._lock:
            return self._events.get(event_id)

    def snapshot_bytes(self, event_id: str) -> Optional[bytes]:
        ev = self.get(event_id)
        return ev.snapshot_frame if ev else None

    def recent(self, limit: int = 100) -> List[Event]:
        with self._lock:
            events = list(self._events.values())
        return events[-limit:][::-1]  # newest first

    def recent_public(self, limit: int = 100) -> List[dict]:
        return [e.to_public() for e in self.recent(limit)]

    def __len__(self) -> int:
        with self._lock:
            return len(self._events)


class EventBroadcaster:
    """Fan-out of new events to connected WebSocket clients.

    Thread-safe `publish()` can be called from the (threaded) analysis workers;
    it schedules delivery onto the asyncio loop the server runs on.
    """

    def __init__(self):
        self._clients: set = set()
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def register(self, ws) -> None:
        with self._lock:
            self._clients.add(ws)

    async def unregister(self, ws) -> None:
        with self._lock:
            self._clients.discard(ws)

    def client_count(self) -> int:
        with self._lock:
            return len(self._clients)

    def publish(self, message: dict) -> None:
        """Schedule a broadcast from any thread."""
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast(message), self._loop)

    async def _broadcast(self, message: dict) -> None:
        with self._lock:
            clients = list(self._clients)
        dead = []
        for ws in clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        if dead:
            with self._lock:
                for ws in dead:
                    self._clients.discard(ws)
