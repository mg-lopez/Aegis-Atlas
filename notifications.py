"""Basic webhook/email notification delivery."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Any

import requests


def send_webhook_notification(webhook_url: str, payload: dict[str, Any], timeout: int = 8) -> dict[str, Any]:
    if not webhook_url:
        return {"channel": "webhook", "status": "skipped", "reason": "missing_webhook_url"}
    try:
        response = requests.post(webhook_url, json=payload, timeout=timeout)
        response.raise_for_status()
        return {
            "channel": "webhook",
            "status": "sent",
            "http_status": response.status_code,
        }
    except Exception as exc:
        return {"channel": "webhook", "status": "failed", "error": str(exc)}


def send_email_notification(email_to: str, subject: str, body: str) -> dict[str, Any]:
    if not email_to:
        return {"channel": "email", "status": "skipped", "reason": "missing_recipient"}

    smtp_host = os.getenv("AEGIS_SMTP_HOST")
    smtp_port = int(os.getenv("AEGIS_SMTP_PORT", "587"))
    smtp_user = os.getenv("AEGIS_SMTP_USER")
    smtp_password = os.getenv("AEGIS_SMTP_PASSWORD")
    smtp_sender = os.getenv("AEGIS_SMTP_SENDER", smtp_user or "aegis-atlas@localhost")

    if not smtp_host:
        return {"channel": "email", "status": "skipped", "reason": "smtp_not_configured"}

    msg = EmailMessage()
    msg["From"] = smtp_sender
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=8) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return {"channel": "email", "status": "sent"}
    except Exception as exc:
        return {"channel": "email", "status": "failed", "error": str(exc)}


def should_notify(threat_level: str) -> bool:
    return threat_level in {"medium", "high"}


def notify_alert(
    alert_payload: dict[str, Any],
    webhook_url: str | None = None,
    email_to: str | None = None,
) -> list[dict[str, Any]]:
    if not should_notify(str(alert_payload.get("threat_level", "none")).lower()):
        return [{"channel": "policy", "status": "skipped", "reason": "threat_below_threshold"}]

    events: list[dict[str, Any]] = []
    if webhook_url:
        events.append(send_webhook_notification(webhook_url, payload=alert_payload))
    if email_to:
        subject = f"Aegis Atlas Alert: {str(alert_payload.get('threat_level', 'unknown')).upper()}"
        body = (
            f"Threat level: {alert_payload.get('threat_level')}\n"
            f"Score: {alert_payload.get('score')}\n"
            f"Confidence: {alert_payload.get('confidence')}\n"
            f"Action: {alert_payload.get('recommended_action')}\n"
        )
        events.append(send_email_notification(email_to=email_to, subject=subject, body=body))
    if not events:
        events.append({"channel": "policy", "status": "skipped", "reason": "no_channels_requested"})
    return events
