"""Utilities for emitting backend domain events."""

from backend.events.event_dispatcher import emit_event
from backend.events.event_types import LEAD_CREATED

__all__ = ["emit_event", "LEAD_CREATED"]
