"""
Shared data models used across the pipeline (adapter -> store -> API -> UI).
"""

from __future__ import annotations

import time
import uuid
from typing import Optional

from pydantic import BaseModel, Field


class Event(BaseModel):
    """A single detected behavior event.

    `snapshot_frame` holds raw JPEG bytes of the triggering frame. It is kept
    server-side (not serialized to the UI); the UI fetches it via
    /snapshot/{id}. `to_public()` returns the JSON-safe view.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    camera_id: str
    camera_name: str
    timestamp: float = Field(default_factory=time.time)
    event_type: str
    confidence: float = 0.0
    severity: str = "low"
    color: str = "#3b82f6"
    description: str = ""

    # Raw JPEG snapshot bytes. Excluded from the public JSON payload.
    snapshot_frame: Optional[bytes] = Field(default=None, repr=False)

    model_config = {"arbitrary_types_allowed": True}

    def to_public(self) -> dict:
        """JSON-safe representation sent to the frontend (no raw image bytes)."""
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "confidence": round(self.confidence, 3),
            "severity": self.severity,
            "color": self.color,
            "description": self.description,
            "has_snapshot": self.snapshot_frame is not None,
        }
