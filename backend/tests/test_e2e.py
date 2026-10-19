"""End-to-end smoke test (Tasks 3 & 9).

Boots the FastAPI app with the mock adapter against a temp config + generated
video, then checks: config endpoint, MJPEG content type, event flow to the
WebSocket, and the snapshot endpoint.
"""

import textwrap
import time

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Generate a tiny looping video.
    vid = tmp_path / "feed1.mp4"
    writer = cv2.VideoWriter(str(vid), cv2.VideoWriter_fourcc(*"mp4v"), 10, (160, 120))
    for i in range(10):
        writer.write(np.full((120, 160, 3), i * 20 % 255, dtype=np.uint8))
    writer.release()

    cfg = tmp_path / "watchlist.yaml"
    cfg.write_text(textwrap.dedent(f"""
    feeds:
      - id: cam-1
        name: "Entrance"
        source: "{vid.as_posix()}"
    watchlist:
      - type: "Loitering"
        description: "lingering"
        severity: medium
    analysis:
      interval_seconds: 0.1
      batch_size: 2
      batch_stride: 1
    model:
      adapter: "mock"
    """), encoding="utf-8")

    import app.config as config_mod
    monkeypatch.setattr(config_mod, "_default_config_path", lambda: str(cfg))

    from app.main import app
    with TestClient(app) as c:
        yield c


def test_config_endpoint(client):
    data = client.get("/api/config").json()
    assert data["feeds"][0]["id"] == "cam-1"
    assert data["watchlist"][0]["type"] == "Loitering"
    assert data["watchlist"][0]["color"].startswith("#")


def test_stream_response_and_generator(client):
    # Verify the stream route returns the MJPEG content type, then drive the
    # async generator directly for a single well-formed chunk. We avoid
    # iterating the live HTTP stream through TestClient because the response
    # is infinite and would deadlock the synchronous test client.
    import asyncio

    from app import main as main_mod

    class _Req:
        def __init__(self, done):
            self._done = done
        async def is_disconnected(self):
            return self._done

    async def _drive():
        resp = await main_mod.stream(_Req(True), "cam-1")
        assert resp.status_code == 200
        ct = resp.headers["content-type"]
        assert "multipart/x-mixed-replace" in ct
        assert "boundary=frame" in ct

        gen = main_mod._mjpeg_generator(_Req(False), "cam-1")
        try:
            for _ in range(100):  # wait for the feed's first frame
                chunk = await gen.__anext__()
                if b"--frame" in chunk and b"image/jpeg" in chunk:
                    return chunk
        finally:
            await gen.aclose()
        return b""

    chunk = asyncio.new_event_loop().run_until_complete(_drive())
    assert b"--frame" in chunk
    assert b"image/jpeg" in chunk


def test_unknown_stream_404(client):
    assert client.get("/stream/nope").status_code == 404


def test_event_flow_and_snapshot(client):
    # Collect events pushed over the WebSocket.
    received = []
    with client.websocket_connect("/ws/events") as ws:
        first = ws.receive_json()
        assert first["type"] == "backlog"
        deadline = time.time() + 8.0
        while time.time() < deadline:
            msg = ws.receive_json()
            if msg["type"] == "event":
                received.append(msg["event"])
                break
    assert received, "no live event received over WebSocket"

    ev = received[0]
    assert ev["event_type"] == "Loitering"
    assert ev["color"].startswith("#")
    if ev["has_snapshot"]:
        img = client.get(f"/snapshot/{ev['id']}")
        assert img.status_code == 200
        assert img.headers["content-type"] == "image/jpeg"
        assert len(img.content) > 0
