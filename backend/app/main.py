"""
FastAPI application wiring everything together (Tasks 3, 6, 9).

Endpoints:
  GET  /api/config          -> feeds + watchlist + severity colors (for the UI)
  GET  /api/status          -> feed + pipeline diagnostics
  GET  /api/events          -> recent events (JSON, newest first)
  GET  /stream/{feed_id}     -> MJPEG live stream for a feed
  GET  /snapshot/{event_id}  -> JPEG snapshot for an event
  WS   /ws/events            -> live event push

Run (from the repo root):
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
or (from backend/):
    uvicorn app.main:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    Response,
    StreamingResponse,
)

# Make the repo root importable so `models.omni_adapter` resolves.
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.abspath(os.path.join(_BACKEND, ".."))
for _p in (_BACKEND, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.config import load_config
from app.event_store import EventBroadcaster, EventStore
from app.pipeline import AnalysisPipeline
from app.video import FeedManager, VideoFeed
from models.omni_adapter import build_adapter


class AppState:
    config = None
    feed_manager: FeedManager = None
    pipeline: AnalysisPipeline = None
    store: EventStore = None
    broadcaster: EventBroadcaster = None


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    state.config = cfg

    # Build feeds.
    fm = FeedManager()
    for f in cfg.feeds:
        source = f.source
        if not os.path.isabs(source):
            source = os.path.join(_REPO_ROOT, source)
        fm.add(VideoFeed(f.id, f.name, source))
    fm.start_all()
    state.feed_manager = fm

    # Event store + broadcaster bound to the running loop.
    store = EventStore()
    broadcaster = EventBroadcaster()
    broadcaster.bind_loop(asyncio.get_running_loop())
    state.store = store
    state.broadcaster = broadcaster

    # Omni adapter (mock by default) + analysis pipeline.
    adapter = build_adapter(cfg.model)
    print(f"[main] using omni adapter: {type(adapter).__name__}")
    pipeline = AnalysisPipeline(
        feeds=fm.all(),
        analyze_fn=adapter.analyze,
        watchlist=cfg.watchlist,
        config=cfg.analysis,
        store=store,
        broadcaster=broadcaster,
    )
    pipeline.start()
    state.pipeline = pipeline

    try:
        yield
    finally:
        pipeline.stop()
        fm.stop_all()


app = FastAPI(title="DGX Spark - Live AI Video Monitoring", lifespan=lifespan)

# Permissive CORS so the React dev server (localhost:5173) can connect.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@app.get("/")
def index():
    """Serve the single-file dashboard (no-cache so edits always show up)."""
    return FileResponse(
        os.path.join(_STATIC_DIR, "index.html"),
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/api/config")
def api_config():
    cfg = state.config
    return {
        "feeds": [{"id": f.id, "name": f.name} for f in cfg.feeds],
        "watchlist": [
            {"type": w.type, "description": w.description,
             "severity": w.severity.value, "color": w.color}
            for w in cfg.watchlist
        ],
    }


@app.get("/api/status")
def api_status():
    return {
        "feeds": state.feed_manager.statuses(),
        "pipeline": state.pipeline.stats(),
        "clients": state.broadcaster.client_count(),
        "events_stored": len(state.store),
    }


@app.get("/api/events")
def api_events(limit: int = 100):
    return {"events": state.store.recent_public(limit)}


async def _mjpeg_generator(request: Request, feed_id: str):
    """Async MJPEG generator that stops as soon as the client disconnects."""
    feed = state.feed_manager.get(feed_id)
    boundary = b"--frame"
    while True:
        if await request.is_disconnected():
            break
        jpeg = feed.latest_jpeg() if feed else None
        if jpeg:
            yield (boundary + b"\r\n"
                   b"Content-Type: image/jpeg\r\n"
                   b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
                   + jpeg + b"\r\n")
        await asyncio.sleep(1 / 20.0)  # ~20 fps cap for the stream


@app.get("/stream/{feed_id}")
async def stream(request: Request, feed_id: str):
    if state.feed_manager.get(feed_id) is None:
        return JSONResponse({"error": "unknown feed"}, status_code=404)
    return StreamingResponse(
        _mjpeg_generator(request, feed_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/snapshot/{event_id}")
def snapshot(event_id: str):
    data = state.store.snapshot_bytes(event_id)
    if not data:
        return JSONResponse({"error": "no snapshot"}, status_code=404)
    return Response(content=data, media_type="image/jpeg")


@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    await state.broadcaster.register(ws)
    # Send a backlog so a freshly opened UI isn't empty.
    try:
        await ws.send_json({"type": "backlog",
                            "events": state.store.recent_public(50)})
        while True:
            await ws.receive_text()  # keep-alive; UI doesn't send much
    except WebSocketDisconnect:
        pass
    finally:
        await state.broadcaster.unregister(ws)
