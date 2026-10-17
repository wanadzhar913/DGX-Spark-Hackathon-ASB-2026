"""Tests for the omni adapter interface + mock (Task 4)."""

import os
import sys

import numpy as np
import pytest

# Put repo root on the path so `models` is importable.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from app.config import Severity, WatchItem
from app.models import Event
from models.omni_adapter import (
    MockOmniAdapter,
    OpenAICompatibleAdapter,
    build_adapter,
    _loads_lenient,
)


def _watchlist():
    return [
        WatchItem(type="Loitering", description="lingering", severity=Severity.medium),
        WatchItem(type="Fighting", description="altercation", severity=Severity.critical),
    ]


def _frames(n=4):
    return [np.full((48, 64, 3), i * 20, dtype=np.uint8) for i in range(n)]


def test_mock_returns_wellformed_events():
    # hit_rate=1 + fixed seed -> deterministic event every call.
    adapter = MockOmniAdapter(hit_rate=1.0, seed=42)
    wl = _watchlist()
    events = adapter.analyze(_frames(), wl, "cam-1", "Entrance")
    assert len(events) == 1
    ev = events[0]
    assert isinstance(ev, Event)
    assert ev.camera_id == "cam-1"
    assert ev.camera_name == "Entrance"
    assert ev.event_type in {w.type for w in wl}
    assert 0.0 <= ev.confidence <= 1.0
    assert ev.severity in {"low", "medium", "high", "critical"}
    assert ev.color.startswith("#")
    assert ev.description
    assert ev.snapshot_frame is not None and len(ev.snapshot_frame) > 0


def test_mock_can_be_quiet():
    adapter = MockOmniAdapter(hit_rate=0.0, seed=1)
    assert adapter.analyze(_frames(), _watchlist(), "c", "C") == []


def test_mock_empty_inputs():
    adapter = MockOmniAdapter(hit_rate=1.0, seed=1)
    assert adapter.analyze([], _watchlist(), "c", "C") == []
    assert adapter.analyze(_frames(), [], "c", "C") == []


def test_event_public_view_hides_bytes():
    adapter = MockOmniAdapter(hit_rate=1.0, seed=7)
    ev = adapter.analyze(_frames(), _watchlist(), "cam-1", "E")[0]
    pub = ev.to_public()
    assert "snapshot_frame" not in pub
    assert pub["has_snapshot"] is True
    assert pub["event_type"] == ev.event_type


def test_build_adapter_mock():
    class M:
        adapter = "mock"
        base_url = ""
        api_key = ""
        model_name = ""
    assert isinstance(build_adapter(M()), MockOmniAdapter)


def test_build_adapter_openai():
    class M:
        adapter = "openai"
        base_url = "http://localhost:8000/v1"
        api_key = "x"
        model_name = "omni"
    assert isinstance(build_adapter(M()), OpenAICompatibleAdapter)


def test_build_adapter_unknown():
    class M:
        adapter = "banana"
        base_url = ""
        api_key = ""
        model_name = ""
    with pytest.raises(ValueError, match="unknown model adapter"):
        build_adapter(M())


def test_openai_parse_lenient_json():
    adapter = OpenAICompatibleAdapter("http://x/v1", "k", "omni")
    text = '```json\n{"events": [{"type": "Fighting", "confidence": 0.9, "description": "two people fighting"}]}\n```'
    events = adapter._parse(text, _frames(), _watchlist(), "cam-2", "Lobby")
    assert len(events) == 1
    assert events[0].event_type == "Fighting"
    assert events[0].severity == "critical"
    assert events[0].confidence == 0.9


def test_openai_parse_ignores_unknown_type():
    adapter = OpenAICompatibleAdapter("http://x/v1", "k", "omni")
    text = '{"events": [{"type": "Dancing", "confidence": 0.9, "description": "x"}]}'
    assert adapter._parse(text, _frames(), _watchlist(), "c", "C") == []


def test_loads_lenient_variants():
    assert _loads_lenient('{"events": []}') == {"events": []}
    assert _loads_lenient('prose {"events": []} more')["events"] == []
    assert _loads_lenient("not json") is None
