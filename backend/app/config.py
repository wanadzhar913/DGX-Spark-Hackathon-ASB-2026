"""
Configuration loading and validation.

Reads `config/watchlist.yaml` and turns it into validated, typed objects the
rest of the app can rely on. Validation errors are raised with clear messages
so a bad config fails fast at startup rather than deep inside the pipeline.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import List

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class ConfigError(Exception):
    """Raised when the configuration file is missing or invalid."""


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# Severity -> color used by the UI badges. Kept here so backend + frontend
# agree on a single source of truth (frontend reads it via /api/config).
SEVERITY_COLORS = {
    Severity.low: "#3b82f6",      # blue
    Severity.medium: "#f59e0b",   # amber
    Severity.high: "#f97316",     # orange
    Severity.critical: "#ef4444", # red
}


class FeedConfig(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)


class WatchItem(BaseModel):
    type: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    severity: Severity

    @property
    def color(self) -> str:
        return SEVERITY_COLORS[self.severity]


class AnalysisConfig(BaseModel):
    interval_seconds: float = Field(4.0, gt=0)
    batch_size: int = Field(4, ge=1, le=32)
    batch_stride: int = Field(5, ge=1)


class ModelConfig(BaseModel):
    model_config = {"protected_namespaces": ()}

    adapter: str = Field("mock", min_length=1)
    base_url: str = "http://localhost:8000/v1"
    api_key: str = "not-needed-for-local"
    model_name: str = "omni"


class AppConfig(BaseModel):
    feeds: List[FeedConfig]
    watchlist: List[WatchItem]
    analysis: AnalysisConfig = AnalysisConfig()
    model: ModelConfig = ModelConfig()

    @field_validator("feeds")
    @classmethod
    def _validate_feeds(cls, feeds: List[FeedConfig]) -> List[FeedConfig]:
        if not feeds:
            raise ValueError("at least one feed must be defined")
        if len(feeds) > 9:
            raise ValueError("a maximum of 9 feeds is supported")
        ids = [f.id for f in feeds]
        if len(ids) != len(set(ids)):
            raise ValueError("feed ids must be unique")
        return feeds

    @field_validator("watchlist")
    @classmethod
    def _validate_watchlist(cls, items: List[WatchItem]) -> List[WatchItem]:
        if not items:
            raise ValueError("watchlist must contain at least one behavior")
        return items


def _default_config_path() -> str:
    # <repo>/backend/app/config.py -> <repo>/config/watchlist.yaml
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    return os.path.join(repo_root, "config", "watchlist.yaml")


def load_config(path: str | None = None) -> AppConfig:
    """Load and validate the app config.

    Raises ConfigError with a human-readable message if the file is missing,
    is not valid YAML, or fails schema validation.
    """
    path = path or _default_config_path()

    if not os.path.exists(path):
        raise ConfigError(f"config file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ConfigError(f"config file is not valid YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping (key: value pairs)")

    try:
        return AppConfig(**raw)
    except ValidationError as exc:
        raise ConfigError(f"config validation failed:\n{exc}") from exc


if __name__ == "__main__":
    # Simple demo: print the parsed config.
    cfg = load_config()
    print("Feeds:")
    for f in cfg.feeds:
        print(f"  [{f.id}] {f.name} <- {f.source}")
    print("\nWatchlist:")
    for w in cfg.watchlist:
        print(f"  {w.type:18s} severity={w.severity.value:8s} color={w.color}")
    print(f"\nAnalysis: {cfg.analysis}")
    print(f"Model: {cfg.model.adapter}")
