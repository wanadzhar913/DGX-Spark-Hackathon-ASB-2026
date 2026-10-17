"""Tests for the looping video feed (Task 2)."""

import time

import cv2
import numpy as np
import pytest

from app.video import FeedManager, VideoFeed


def _make_video(path, n_frames=10, w=160, h=120, fps=10):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (w, h))
    for i in range(n_frames):
        frame = np.full((h, w, 3), i * 10 % 255, dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return str(path)


def _wait(cond, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if cond():
            return True
        time.sleep(0.05)
    return False


def test_feed_serves_and_loops(tmp_path):
    path = _make_video(tmp_path / "clip.mp4", n_frames=8)
    feed = VideoFeed("cam-1", "Test", path, buffer_size=32, target_fps=50)
    feed.start()
    try:
        assert _wait(lambda: feed.latest_jpeg() is not None), "no frame served"
        assert feed.available is True
        # Serve more than one clip length -> must have looped.
        assert _wait(lambda: feed.loops >= 1), "feed did not loop"
        assert feed.frame_index > 8
    finally:
        feed.stop()


def test_recent_frames_buffer(tmp_path):
    path = _make_video(tmp_path / "clip.mp4", n_frames=20)
    feed = VideoFeed("cam-1", "Test", path, buffer_size=16, target_fps=50)
    feed.start()
    try:
        assert _wait(lambda: len(feed.recent_frames(16)) >= 4)
        batch = feed.recent_frames(4, stride=2)
        assert 1 <= len(batch) <= 4
        for f in batch:
            assert isinstance(f, np.ndarray)
    finally:
        feed.stop()


def test_missing_file_degrades_gracefully():
    feed = VideoFeed("cam-x", "Ghost", "does_not_exist.mp4", target_fps=50)
    feed.start()
    try:
        # Still produces a (placeholder) frame rather than crashing.
        assert _wait(lambda: feed.latest_jpeg() is not None)
        assert feed.available is False
    finally:
        feed.stop()


def test_feed_manager(tmp_path):
    path = _make_video(tmp_path / "clip.mp4", n_frames=6)
    mgr = FeedManager()
    mgr.add(VideoFeed("a", "A", path, target_fps=50))
    mgr.add(VideoFeed("b", "B", path, target_fps=50))
    mgr.start_all()
    try:
        assert len(mgr.all()) == 2
        assert mgr.get("a") is not None
        assert _wait(lambda: all(s["buffered"] > 0 for s in mgr.statuses()))
    finally:
        mgr.stop_all()
