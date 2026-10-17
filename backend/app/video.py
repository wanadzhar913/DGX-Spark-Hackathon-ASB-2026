"""
Video feed source.

Each `VideoFeed` opens a video file and loops it forever in a background
thread, simulating a live camera. It exposes:
  - `latest_jpeg()`  : the most recent frame as JPEG bytes (for MJPEG streaming)
  - `recent_frames()`: a rolling buffer of recent raw frames (for analysis)

Missing / unreadable files degrade gracefully to a generated placeholder frame
so the wall still renders during a demo even if a clip is absent.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Deque, List, Optional

import cv2
import numpy as np


class VideoFeed:
    def __init__(
        self,
        feed_id: str,
        name: str,
        source: str,
        buffer_size: int = 64,
        target_fps: float = 20.0,
        frame_width: int = 640,
    ):
        self.feed_id = feed_id
        self.name = name
        self.source = source
        self.target_fps = target_fps
        self.frame_width = frame_width

        self._buffer: Deque[np.ndarray] = deque(maxlen=buffer_size)
        self._latest_jpeg: Optional[bytes] = None
        self._frame_index = 0          # total frames served (monotonic)
        self._loops = 0                # how many times the clip has wrapped
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._available = False        # True if the source opened successfully

    # ---- lifecycle -------------------------------------------------------

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    # ---- capture loop ----------------------------------------------------

    def _run(self) -> None:
        cap = cv2.VideoCapture(self.source)
        self._available = cap.isOpened()
        frame_interval = 1.0 / self.target_fps if self.target_fps > 0 else 0.0

        while self._running:
            start = time.time()

            if not self._available:
                frame = self._placeholder("NO SIGNAL")
                self._publish(frame)
                time.sleep(0.1)
                continue

            ok, frame = cap.read()
            if not ok:
                # End of file -> loop back to the start.
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self._loops += 1
                ok, frame = cap.read()
                if not ok:
                    # Unreadable even after rewind; treat as unavailable.
                    self._available = False
                    continue

            frame = self._resize(frame)
            self._publish(frame)

            elapsed = time.time() - start
            if frame_interval > elapsed:
                time.sleep(frame_interval - elapsed)

        cap.release()

    # ---- helpers ---------------------------------------------------------

    def _resize(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        if w <= 0:
            return frame
        scale = self.frame_width / float(w)
        if scale < 1.0:
            frame = cv2.resize(frame, (self.frame_width, int(h * scale)))
        return frame

    def _publish(self, frame: np.ndarray) -> None:
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        with self._lock:
            self._buffer.append(frame)
            if ok:
                self._latest_jpeg = buf.tobytes()
            self._frame_index += 1

    def _placeholder(self, text: str) -> np.ndarray:
        h, w = 360, self.frame_width
        img = np.zeros((h, w, 3), dtype=np.uint8)
        img[:] = (30, 30, 30)
        cv2.putText(img, self.name, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (200, 200, 200), 2)
        cv2.putText(img, text, (20, h // 2), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (0, 0, 255), 2)
        return img

    # ---- accessors -------------------------------------------------------

    def latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    def recent_frames(self, count: int, stride: int = 1) -> List[np.ndarray]:
        """Return up to `count` recent frames, every `stride`-th frame.

        Newest-last ordering (chronological) so the model sees motion in time.
        """
        stride = max(1, stride)
        with self._lock:
            frames = list(self._buffer)
        if not frames:
            return []
        picked = frames[::-1][:: stride][:count]  # newest-first, strided
        return list(reversed(picked))             # back to chronological

    @property
    def frame_index(self) -> int:
        with self._lock:
            return self._frame_index

    @property
    def loops(self) -> int:
        with self._lock:
            return self._loops

    @property
    def available(self) -> bool:
        return self._available

    def status(self) -> dict:
        with self._lock:
            return {
                "id": self.feed_id,
                "name": self.name,
                "source": self.source,
                "available": self._available,
                "frame_index": self._frame_index,
                "loops": self._loops,
                "buffered": len(self._buffer),
            }


class FeedManager:
    """Owns all `VideoFeed` instances and their lifecycle."""

    def __init__(self):
        self._feeds: dict[str, VideoFeed] = {}

    def add(self, feed: VideoFeed) -> None:
        self._feeds[feed.feed_id] = feed

    def get(self, feed_id: str) -> Optional[VideoFeed]:
        return self._feeds.get(feed_id)

    def all(self) -> List[VideoFeed]:
        return list(self._feeds.values())

    def start_all(self) -> None:
        for f in self._feeds.values():
            f.start()

    def stop_all(self) -> None:
        for f in self._feeds.values():
            f.stop()

    def statuses(self) -> List[dict]:
        return [f.status() for f in self._feeds.values()]
