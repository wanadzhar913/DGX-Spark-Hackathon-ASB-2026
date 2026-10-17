"""Tests for the analysis pipeline: batching, backpressure, store wiring (Task 5)."""

import time

import numpy as np
import pytest

from app.config import AnalysisConfig, Severity, WatchItem
from app.event_store import EventStore
from app.models import Event
from app.pipeline import AnalysisPipeline


class _FakeFeed:
    """Minimal stand-in for VideoFeed exposing recent_frames()."""

    def __init__(self, feed_id, name):
        self.feed_id = feed_id
        self.name = name

    def recent_frames(self, count, stride=1):
        return [np.zeros((8, 8, 3), dtype=np.uint8) for _ in range(count)]


def _watchlist():
    return [WatchItem(type="Loitering", description="x", severity=Severity.medium)]


def _wait(cond, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if cond():
            return True
        time.sleep(0.02)
    return False


def test_events_land_in_store():
    store = EventStore()

    def analyze(frames, watchlist, cam_id, cam_name):
        assert len(frames) == 3
        return [Event(camera_id=cam_id, camera_name=cam_name,
                      event_type="Loitering", confidence=0.9)]

    cfg = AnalysisConfig(interval_seconds=0.05, batch_size=3, batch_stride=1)
    pipe = AnalysisPipeline([_FakeFeed("cam-1", "C")], analyze, _watchlist(),
                            cfg, store, num_workers=2)
    pipe.start()
    try:
        assert _wait(lambda: len(store) >= 1), "no events produced"
    finally:
        pipe.stop()
    assert pipe.stats()["produced"] >= 1


def test_backpressure_drops_stale_jobs():
    store = EventStore()
    started = {"n": 0}

    def slow_analyze(frames, watchlist, cam_id, cam_name):
        started["n"] += 1
        time.sleep(0.3)  # slower than the scheduler interval
        return []

    # Fast scheduler + single slow worker + tiny queue => drops must occur.
    cfg = AnalysisConfig(interval_seconds=0.02, batch_size=2, batch_stride=1)
    pipe = AnalysisPipeline([_FakeFeed("cam-1", "C")], slow_analyze, _watchlist(),
                            cfg, store, num_workers=1, max_pending=1)
    pipe.start()
    try:
        assert _wait(lambda: pipe.stats()["dropped"] >= 1, timeout=5.0), \
            "expected stale jobs to be dropped under load"
    finally:
        pipe.stop()


def test_analyze_exception_does_not_crash_worker():
    store = EventStore()
    calls = {"n": 0}

    def flaky(frames, watchlist, cam_id, cam_name):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return [Event(camera_id=cam_id, camera_name=cam_name,
                      event_type="Loitering", confidence=0.5)]

    cfg = AnalysisConfig(interval_seconds=0.05, batch_size=2, batch_stride=1)
    pipe = AnalysisPipeline([_FakeFeed("cam-1", "C")], flaky, _watchlist(),
                            cfg, store, num_workers=1)
    pipe.start()
    try:
        # Despite the first call raising, the worker survives and later events land.
        assert _wait(lambda: len(store) >= 1, timeout=5.0)
    finally:
        pipe.stop()
