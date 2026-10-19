"""Tests for the in-memory event store (Task 6)."""

from app.event_store import EventStore
from app.models import Event


def _ev(**kw):
    return Event(camera_id="cam-1", camera_name="C", event_type="Loitering", **kw)


def test_add_and_get():
    store = EventStore()
    ev = _ev(snapshot_frame=b"jpegbytes")
    store.add(ev)
    assert len(store) == 1
    assert store.get(ev.id) is ev
    assert store.snapshot_bytes(ev.id) == b"jpegbytes"


def test_recent_newest_first():
    store = EventStore()
    ids = []
    for i in range(5):
        e = _ev(description=f"e{i}")
        store.add(e)
        ids.append(e.id)
    recent = store.recent()
    assert [e.id for e in recent] == list(reversed(ids))


def test_capacity_drops_oldest():
    store = EventStore(capacity=3)
    kept = []
    for i in range(5):
        e = _ev(description=f"e{i}")
        store.add(e)
        kept.append(e.id)
    assert len(store) == 3
    # First two should have been evicted.
    assert store.get(kept[0]) is None
    assert store.get(kept[1]) is None
    assert store.get(kept[-1]) is not None


def test_public_view():
    store = EventStore()
    store.add(_ev(snapshot_frame=b"x"))
    pub = store.recent_public()[0]
    assert "snapshot_frame" not in pub
    assert pub["has_snapshot"] is True
