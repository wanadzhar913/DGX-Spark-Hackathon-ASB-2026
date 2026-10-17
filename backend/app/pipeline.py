"""
Analysis pipeline (Task 5).

For each feed, a lightweight scheduler thread periodically grabs a short batch
of recent frames and enqueues an analysis job. A pool of worker threads runs
the (potentially slow) omni adapter so video playback is never blocked.

Backpressure: the job queue has `maxsize=1` per feed-less design via a single
bounded queue. When a worker is busy and a new batch arrives, the oldest
pending job is dropped so we always analyze *fresh* frames rather than piling
up stale work.
"""

from __future__ import annotations

import queue
import threading
import time
from typing import Callable, List, Optional

import numpy as np

from .config import AnalysisConfig, WatchItem
from .event_store import EventBroadcaster, EventStore
from .models import Event
from .video import VideoFeed


class _Job:
    __slots__ = ("feed_id", "feed_name", "frames", "created")

    def __init__(self, feed_id, feed_name, frames):
        self.feed_id = feed_id
        self.feed_name = feed_name
        self.frames = frames
        self.created = time.time()


class AnalysisPipeline:
    def __init__(
        self,
        feeds: List[VideoFeed],
        analyze_fn: Callable[[List[np.ndarray], List[WatchItem], str, str], List[Event]],
        watchlist: List[WatchItem],
        config: AnalysisConfig,
        store: EventStore,
        broadcaster: Optional[EventBroadcaster] = None,
        num_workers: int = 2,
        max_pending: int = 4,
    ):
        self.feeds = feeds
        self.analyze_fn = analyze_fn
        self.watchlist = watchlist
        self.config = config
        self.store = store
        self.broadcaster = broadcaster
        self.num_workers = num_workers

        self._queue: "queue.Queue[_Job]" = queue.Queue(maxsize=max_pending)
        self._running = False
        self._threads: List[threading.Thread] = []
        self._dropped = 0
        self._produced = 0

    # ---- lifecycle -------------------------------------------------------

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        for feed in self.feeds:
            t = threading.Thread(target=self._schedule_loop, args=(feed,), daemon=True)
            t.start()
            self._threads.append(t)
        for _ in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self) -> None:
        self._running = False
        for t in self._threads:
            t.join(timeout=2.0)
        self._threads.clear()

    # ---- scheduling ------------------------------------------------------

    def _schedule_loop(self, feed: VideoFeed) -> None:
        while self._running:
            time.sleep(self.config.interval_seconds)
            if not self._running:
                break
            frames = feed.recent_frames(self.config.batch_size,
                                        stride=self.config.batch_stride)
            if not frames:
                continue
            self._enqueue(_Job(feed.feed_id, feed.name, frames))

    def _enqueue(self, job: _Job) -> None:
        """Enqueue a job, dropping the oldest pending job if the queue is full."""
        try:
            self._queue.put_nowait(job)
        except queue.Full:
            try:
                self._queue.get_nowait()  # drop stale
                self._dropped += 1
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(job)
            except queue.Full:
                self._dropped += 1

    # ---- workers ---------------------------------------------------------

    def _worker_loop(self) -> None:
        while self._running:
            try:
                job = self._queue.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                events = self.analyze_fn(
                    job.frames, self.watchlist, job.feed_id, job.feed_name
                )
            except Exception as exc:  # never let a model error kill the worker
                print(f"[pipeline] analyze failed for {job.feed_id}: {exc}")
                events = []
            for ev in events or []:
                self._produced += 1
                self.store.add(ev)
                if self.broadcaster is not None:
                    self.broadcaster.publish({"type": "event", "event": ev.to_public()})

    # ---- introspection (for the debug endpoint / tests) ------------------

    def stats(self) -> dict:
        return {
            "running": self._running,
            "workers": self.num_workers,
            "pending": self._queue.qsize(),
            "dropped": self._dropped,
            "produced": self._produced,
        }
