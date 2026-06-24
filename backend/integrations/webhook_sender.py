"""Webhook sender for external automation systems."""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT_SECONDS = 5.0


def send_event_webhook(event: dict) -> None:
    """Send a domain event to the configured webhook endpoint."""
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    if not webhook_url:
        logger.error("webhook_send_failed", extra={"reason": "missing_webhook_url"})
        return

    headers = {"Content-Type": "application/json"}
    webhook_token = os.getenv("N8N_WEBHOOK_TOKEN")
    if webhook_token:
        headers["X-Webhook-Token"] = webhook_token

    try:
        response = httpx.post(
            webhook_url,
            json=event,
            headers=headers,
            timeout=WEBHOOK_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("webhook_send_failed", extra={"url": webhook_url, "event": event})
        return

    logger.info(
        "webhook_send_succeeded",
        extra={"url": webhook_url, "status_code": response.status_code},
    )


__all__ = ["send_event_webhook"]
