"""
=============================================================================
 OMNI MODEL ADAPTER  --  THIS IS WHERE YOU PLUG IN YOUR DGX SPARK OMNI MODEL
=============================================================================

The rest of the application only knows about the `OmniAdapter` interface:

    adapter.analyze(frames, watchlist, camera_id, camera_name) -> list[Event]

`frames` is a short chronological clip (list of BGR numpy arrays) giving the
model temporal context. `watchlist` is the list of behaviors to look for (from
config/watchlist.yaml). The adapter returns zero or more `Event` objects.

Two implementations ship here:

  1. MockOmniAdapter          -> fake-but-realistic events, no GPU. Default so
                                 the whole dashboard is demoable immediately.
  2. OpenAICompatibleAdapter  -> talks to a local OpenAI-compatible server
                                 (vLLM / Ollama / etc.) serving your omni model.
                                 >>> Fill in the two TODOs and set
                                     model.adapter: "openai" in the config. <<<

To add a totally different serving method, subclass `OmniAdapter`, implement
`analyze(...)`, and register it in `build_adapter(...)` at the bottom.
"""

from __future__ import annotations

import base64
import json
import random
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Sequence

import cv2
import numpy as np

# Import path works whether the app is launched from the repo root or backend/.
# `app.*` is tried first so the Event class is the SAME module object the
# backend uses (avoids duplicate-class isinstance mismatches).
try:
    from app.models import Event
    from app.config import WatchItem, SEVERITY_COLORS, Severity
except ImportError:  # when only the repo root is on sys.path
    from backend.app.models import Event
    from backend.app.config import WatchItem, SEVERITY_COLORS, Severity


# --------------------------------------------------------------------------
# Interface
# --------------------------------------------------------------------------

class OmniAdapter(ABC):
    """Interface every omni backend must implement."""

    @abstractmethod
    def analyze(
        self,
        frames: Sequence[np.ndarray],
        watchlist: List[WatchItem],
        camera_id: str,
        camera_name: str,
    ) -> List[Event]:
        """Analyze a short clip and return detected events (possibly empty)."""
        raise NotImplementedError


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

def encode_jpeg(frame: np.ndarray, quality: int = 80) -> bytes:
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes() if ok else b""


def encode_data_url(frame: np.ndarray, quality: int = 80) -> str:
    jpeg = encode_jpeg(frame, quality)
    b64 = base64.b64encode(jpeg).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _watch_by_type(watchlist: List[WatchItem], event_type: str) -> Optional[WatchItem]:
    for w in watchlist:
        if w.type.lower() == str(event_type).lower():
            return w
    return None


def _make_event(
    watch: WatchItem,
    camera_id: str,
    camera_name: str,
    description: str,
    confidence: float,
    snapshot: Optional[np.ndarray],
) -> Event:
    return Event(
        camera_id=camera_id,
        camera_name=camera_name,
        event_type=watch.type,
        confidence=float(confidence),
        severity=watch.severity.value,
        color=watch.color,
        description=description,
        snapshot_frame=encode_jpeg(snapshot) if snapshot is not None else None,
    )


# --------------------------------------------------------------------------
# 1. Mock adapter  (default -- no model required)
# --------------------------------------------------------------------------

class MockOmniAdapter(OmniAdapter):
    """Produces plausible fake events so the pipeline + UI are demoable.

    On each call it *may* emit an event (controlled by `hit_rate`), choosing a
    random behavior from the watchlist and generating a short description.
    """

    _TEMPLATES = {
        "default": [
            "{subject} detected near the {place}.",
            "Possible {type_lower} observed in view of {camera}.",
            "{subject} exhibiting behavior consistent with {type_lower}.",
        ],
    }
    _SUBJECTS = ["A person", "An individual", "Two people", "A small group"]
    _PLACES = ["entrance", "walkway", "parked vehicles", "doorway", "far corner"]

    def __init__(self, hit_rate: float = 0.6, seed: Optional[int] = None):
        self.hit_rate = hit_rate
        self._rng = random.Random(seed)

    def analyze(self, frames, watchlist, camera_id, camera_name) -> List[Event]:
        if not watchlist or not frames:
            return []
        if self._rng.random() > self.hit_rate:
            return []  # nothing noteworthy this pass

        watch = self._rng.choice(watchlist)
        template = self._rng.choice(self._TEMPLATES["default"])
        description = template.format(
            subject=self._rng.choice(self._SUBJECTS),
            place=self._rng.choice(self._PLACES),
            type_lower=watch.type.lower(),
            camera=camera_name,
        )
        confidence = round(self._rng.uniform(0.55, 0.98), 3)
        snapshot = frames[-1]  # the triggering (most recent) frame
        return [_make_event(watch, camera_id, camera_name,
                            description, confidence, snapshot)]


# --------------------------------------------------------------------------
# 2. OpenAI-compatible adapter  (suggested real integration)
# --------------------------------------------------------------------------

class OpenAICompatibleAdapter(OmniAdapter):
    """Calls a local OpenAI-compatible chat endpoint serving your omni model.

    Works with vLLM, Ollama, llama.cpp server, etc. The frames are sent as a
    multi-image message; the model is asked to return strict JSON describing
    any watchlist behaviors it sees.

    >>> TO ENABLE:
        1. Serve your omni model with an OpenAI-compatible API on the Spark.
        2. Set model.adapter: "openai" and model.base_url/model_name in
           config/watchlist.yaml.
        3. Adjust the prompt / payload below for your specific model if needed
           (see the two TODO markers).
    """

    def __init__(self, base_url: str, api_key: str, model_name: str,
                 timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout

    def _build_prompt(self, watchlist: List[WatchItem], camera_name: str) -> str:
        behaviors = "\n".join(
            f'- "{w.type}": {w.description}' for w in watchlist
        )
        # TODO (model-specific): tune this prompt for your omni model.
        return (
            f"You are a CCTV behavior-analysis assistant monitoring camera "
            f'"{camera_name}". The images are consecutive frames of a short '
            f"clip. Determine whether any of these behaviors are occurring:\n"
            f"{behaviors}\n\n"
            "Respond ONLY with a JSON object of the form:\n"
            '{"events": [{"type": "<one of the behavior names>", '
            '"confidence": <0..1>, "description": "<one short sentence>"}]}\n'
            "If nothing noteworthy is happening, return "
            '{"events": []}. Do not include any text outside the JSON.'
        )

    def _build_payload(self, frames, watchlist, camera_name) -> dict:
        content = [{"type": "text", "text": self._build_prompt(watchlist, camera_name)}]
        for frame in frames:
            content.append({
                "type": "image_url",
                "image_url": {"url": encode_data_url(frame)},
            })
        # TODO (model-specific): some servers want "max_tokens", others
        # "max_completion_tokens", and some omni models accept a "video" input
        # type instead of multiple images. Adjust as needed.
        return {
            "model": self.model_name,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.2,
            "max_tokens": 400,
        }

    def analyze(self, frames, watchlist, camera_id, camera_name) -> List[Event]:
        if not frames or not watchlist:
            return []

        import httpx  # local import so the mock path needs no network deps

        payload = self._build_payload(frames, watchlist, camera_name)
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload, headers=headers, timeout=self.timeout,
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:  # degrade gracefully; never crash the stream
            print(f"[OpenAICompatibleAdapter] request failed: {exc}")
            return []

        return self._parse(text, frames, watchlist, camera_id, camera_name)

    def _parse(self, text, frames, watchlist, camera_id, camera_name) -> List[Event]:
        data = _loads_lenient(text)
        if not isinstance(data, dict):
            return []
        events = data.get("events") or []
        if not isinstance(events, list):
            return []
        out: List[Event] = []
        snapshot = frames[-1]
        for item in events:
            if not isinstance(item, dict):
                continue
            watch = _watch_by_type(watchlist, item.get("type") or "")
            if watch is None:
                continue
            # The model may send null / missing fields; coerce safely so a
            # single odd item never crashes the whole batch.
            raw_desc = item.get("description")
            description = str(raw_desc).strip() if raw_desc is not None else ""
            try:
                confidence = float(item.get("confidence") or 0.0)
            except (TypeError, ValueError):
                confidence = 0.0
            out.append(_make_event(
                watch, camera_id, camera_name,
                description=description,
                confidence=confidence,
                snapshot=snapshot,
            ))
        return out


def _loads_lenient(text: str) -> Optional[dict]:
    """Parse JSON, tolerating markdown fences / surrounding prose."""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                text = p
                break
    # Fall back to the first {...} span.
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------------
# Factory
# --------------------------------------------------------------------------

def build_adapter(model_cfg) -> OmniAdapter:
    """Instantiate the adapter named in config (`model.adapter`)."""
    name = (model_cfg.adapter or "mock").lower()
    if name == "mock":
        return MockOmniAdapter()
    if name in ("openai", "openai_compatible", "vllm", "ollama"):
        return OpenAICompatibleAdapter(
            base_url=model_cfg.base_url,
            api_key=model_cfg.api_key,
            model_name=model_cfg.model_name,
        )
    raise ValueError(
        f"unknown model adapter '{model_cfg.adapter}'. "
        f"Use 'mock' or 'openai', or register a new one in build_adapter()."
    )
