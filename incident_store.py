"""Lightweight JSON-backed incident queue persistence."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

INCIDENTS_FILE = Path(__file__).resolve().parent / "data" / "incidents.json"


def _ensure_parent() -> None:
    INCIDENTS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_all() -> list[dict[str, Any]]:
    if not INCIDENTS_FILE.exists():
        return []
    try:
        data = json.loads(INCIDENTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _save_all(items: list[dict[str, Any]]) -> None:
    _ensure_parent()
    INCIDENTS_FILE.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")


def list_incidents() -> list[dict[str, Any]]:
    return _load_all()


def get_incident(incident_id: str) -> dict[str, Any] | None:
    for item in _load_all():
        if str(item.get("id", "")) == str(incident_id):
            return item
    return None


def find_open_incident_by_analysis_key(analysis_key: str) -> dict[str, Any] | None:
    for item in _load_all():
        if item.get("status") != "open":
            continue
        if str(item.get("analysis_key", "")) == str(analysis_key):
            return item
    return None


def create_incident(entry: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    incident = {
        "id": str(uuid.uuid4()),
        "status": "open",
        "created_at": now,
        "updated_at": now,
        "closed_at": None,
        "last_exported_at": None,
        "last_export_format": None,
        **entry,
    }
    items = _load_all()
    items.append(incident)
    _save_all(items)
    return incident


def update_incident(incident_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = _load_all()
    updated: dict[str, Any] | None = None
    for index, item in enumerate(items):
        if str(item.get("id", "")) != str(incident_id):
            continue
        updated = {
            **item,
            **updates,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        items[index] = updated
        break
    if updated is None:
        return None
    _save_all(items)
    return updated


def close_incident(incident_id: str) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc).isoformat()
    return update_incident(
        incident_id,
        {
            "status": "closed",
            "closed_at": now,
        },
    )
