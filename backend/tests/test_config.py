"""Tests for config loading and validation (Task 1)."""

import textwrap

import pytest

from app.config import ConfigError, Severity, load_config


def _write(tmp_path, content: str):
    p = tmp_path / "watchlist.yaml"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(p)


VALID = """
feeds:
  - id: cam-1
    name: "Entrance"
    source: "videos/feed1.mp4"
watchlist:
  - type: "Loitering"
    description: "Person lingering."
    severity: medium
analysis:
  interval_seconds: 2.0
  batch_size: 3
  batch_stride: 4
model:
  adapter: "mock"
"""


def test_loads_valid_config(tmp_path):
    cfg = load_config(_write(tmp_path, VALID))
    assert len(cfg.feeds) == 1
    assert cfg.feeds[0].id == "cam-1"
    assert cfg.watchlist[0].severity == Severity.medium
    assert cfg.watchlist[0].color.startswith("#")
    assert cfg.analysis.batch_size == 3
    assert cfg.model.adapter == "mock"


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(str(tmp_path / "nope.yaml"))


def test_invalid_yaml_raises(tmp_path):
    p = _write(tmp_path, "feeds: [unterminated\n")
    with pytest.raises(ConfigError, match="not valid YAML"):
        load_config(p)


def test_no_feeds_raises(tmp_path):
    bad = """
    feeds: []
    watchlist:
      - type: "Loitering"
        description: "x"
        severity: low
    """
    with pytest.raises(ConfigError, match="at least one feed"):
        load_config(_write(tmp_path, bad))


def test_too_many_feeds_raises(tmp_path):
    feeds = "\n".join(
        f'  - id: cam-{i}\n    name: "C{i}"\n    source: "v{i}.mp4"'
        for i in range(5)
    )
    bad = f"""
feeds:
{feeds}
watchlist:
  - type: "Loitering"
    description: "x"
    severity: low
"""
    with pytest.raises(ConfigError, match="maximum of 4"):
        load_config(_write(tmp_path, bad))


def test_duplicate_feed_ids_raise(tmp_path):
    bad = """
    feeds:
      - id: cam-1
        name: "A"
        source: "a.mp4"
      - id: cam-1
        name: "B"
        source: "b.mp4"
    watchlist:
      - type: "Loitering"
        description: "x"
        severity: low
    """
    with pytest.raises(ConfigError, match="unique"):
        load_config(_write(tmp_path, bad))


def test_bad_severity_raises(tmp_path):
    bad = """
    feeds:
      - id: cam-1
        name: "A"
        source: "a.mp4"
    watchlist:
      - type: "Loitering"
        description: "x"
        severity: catastrophic
    """
    with pytest.raises(ConfigError, match="validation failed"):
        load_config(_write(tmp_path, bad))


def test_missing_watchlist_field_raises(tmp_path):
    bad = """
    feeds:
      - id: cam-1
        name: "A"
        source: "a.mp4"
    watchlist:
      - type: "Loitering"
        severity: low
    """
    with pytest.raises(ConfigError, match="validation failed"):
        load_config(_write(tmp_path, bad))
