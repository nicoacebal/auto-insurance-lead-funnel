"""Minimal domain event dispatcher."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from backend.integrations.webhook_sender import send_event_webhook

logger = logging.getLogger(__name__)

EVENT_VERSION = "1"
EVENT_SOURCE = "auto-insurance-lead-funnel"


def emit_event(event_type: str, payload: dict) -> dict:
    """Build, log, and return a domain event."""
    event = {
        "event_type": event_type,
        "event_version": EVENT_VERSION,
        "event_id": str(uuid4()),
        "occurred_at": datetime.now(UTC).isoformat(),
        "source": EVENT_SOURCE,
        "data": payload,
    }

    logger.info("Domain event emitted", extra={"event": event})

    try:
        send_event_webhook(event)
    except Exception:
        logger.exception("Failed to deliver event webhook")

    return event
