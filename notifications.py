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


def send_email_notification(
    email_to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> dict[str, Any]:
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
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=8) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return {"channel": "email", "status": "sent"}
    except Exception as exc:
        return {"channel": "email", "status": "failed", "error": str(exc)}


def send_sms_notification(phone_to: str, message: str, timeout: int = 8) -> dict[str, Any]:
    if not phone_to:
        return {"channel": "sms", "status": "skipped", "reason": "missing_recipient"}

    sms_webhook_url = os.getenv("AEGIS_SMS_WEBHOOK_URL")
    if not sms_webhook_url:
        return {"channel": "sms", "status": "skipped", "reason": "sms_not_configured"}

    try:
        response = requests.post(
            sms_webhook_url,
            json={"to": phone_to, "message": message},
            timeout=timeout,
        )
        response.raise_for_status()
        return {
            "channel": "sms",
            "status": "sent",
            "http_status": response.status_code,
        }
    except Exception as exc:
        return {"channel": "sms", "status": "failed", "error": str(exc)}


def should_notify(threat_level: str, minimum_level: str = "medium") -> bool:
    priority = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    normalized_level = str(threat_level or "none").lower()
    normalized_minimum = str(minimum_level or "medium").lower()
    return priority.get(normalized_level, 0) >= priority.get(normalized_minimum, 2)


def notify_alert(
    alert_payload: dict[str, Any],
    webhook_url: str | None = None,
    email_to: str | None = None,
    html_body: str | None = None,
    sms_to: str | None = None,
    sms_message: str | None = None,
    minimum_level: str = "medium",
) -> list[dict[str, Any]]:
    if not should_notify(str(alert_payload.get("threat_level", "none")).lower(), minimum_level=minimum_level):
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
        events.append(send_email_notification(email_to=email_to, subject=subject, body=body, html_body=html_body))
    if sms_to:
        message = sms_message or (
            f"Aegis Atlas {str(alert_payload.get('threat_level', 'unknown')).upper()} alert "
            f"score={alert_payload.get('score')} action={alert_payload.get('recommended_action')}"
        )
        events.append(send_sms_notification(phone_to=sms_to, message=message))
    if not events:
        events.append({"channel": "policy", "status": "skipped", "reason": "no_channels_requested"})
    return events
