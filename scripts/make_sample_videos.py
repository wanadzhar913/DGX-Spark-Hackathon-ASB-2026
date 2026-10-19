"""
Generate placeholder sample videos so the dashboard has something to play
out of the box. Replace the files in `videos/` with real CCTV clips anytime.

Usage (from repo root):
    backend/.venv/Scripts/python scripts/make_sample_videos.py
"""

import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(REPO, "videos")

SCENES = [
    ("feed1.mp4", (25, 35, 55), "ENTRANCE - NORTH"),
    ("feed2.mp4", (45, 30, 30), "CAR PARK - LEVEL 2"),
    ("feed3.mp4", (30, 45, 35), "LOBBY"),
    ("feed4.mp4", (40, 40, 25), "REAR ALLEY"),
]

W, H, FPS, SECONDS = 640, 360, 20, 8


def make(path, bg, title):
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    total = FPS * SECONDS
    for i in range(total):
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:] = bg
        # Faux timestamp overlay.
        cv2.putText(frame, f"{title}", (16, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (210, 210, 210), 2)
        cv2.putText(frame, f"CAM  t={i/FPS:05.2f}s", (16, H - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        # A "person" (moving circle) walking across the scene.
        x = int((i / total) * (W + 80)) - 40
        cv2.circle(frame, (x, H // 2 + 40), 16, (235, 235, 235), -1)
        cv2.rectangle(frame, (x - 10, H // 2 + 55), (x + 10, H // 2 + 95),
                      (90, 120, 200), -1)
        # Grid lines for a CCTV feel.
        for gx in range(0, W, 80):
            cv2.line(frame, (gx, 0), (gx, H), (255, 255, 255), 1, cv2.LINE_AA)
        writer.write(frame)
    writer.release()
    print(f"  wrote {path}")


def main():
    os.makedirs(OUT, exist_ok=True)
    print(f"Generating sample videos into {OUT}")
    for name, bg, title in SCENES:
        make(os.path.join(OUT, name), bg, title)
    print("Done. Replace these with real clips anytime.")


if __name__ == "__main__":
    main()
