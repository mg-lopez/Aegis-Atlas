"""Simple JSON-backed family watchlist persistence."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WATCHLISTS_FILE = Path(__file__).resolve().parent / "data" / "watchlists.json"


def _ensure_parent() -> None:
    WATCHLISTS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_all() -> list[dict[str, Any]]:
    if not WATCHLISTS_FILE.exists():
        return []
    try:
        data = json.loads(WATCHLISTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _save_all(items: list[dict[str, Any]]) -> None:
    _ensure_parent()
    WATCHLISTS_FILE.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")


def list_watchlists() -> list[dict[str, Any]]:
    return _load_all()


def create_watchlist(name: str, members: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    watchlist = {
        "id": str(uuid.uuid4()),
        "name": str(name).strip() or "Untitled Watchlist",
        "members": members,
        "alerts": {},
        "created_at": now,
        "updated_at": now,
    }
    existing = _load_all()
    existing.append(watchlist)
    _save_all(existing)
    return watchlist


def get_watchlist(watchlist_id: str) -> dict[str, Any] | None:
    for item in _load_all():
        if item.get("id") == watchlist_id:
            return item
    return None


def update_watchlist_alerts(watchlist_id: str, alerts: dict[str, Any]) -> dict[str, Any] | None:
    existing = _load_all()
    now = datetime.now(timezone.utc).isoformat()
    for item in existing:
        if item.get("id") != watchlist_id:
            continue
        item["alerts"] = alerts
        item["updated_at"] = now
        _save_all(existing)
        return item
    return None


def delete_watchlist(watchlist_id: str) -> dict[str, Any] | None:
    existing = _load_all()
    remaining = [item for item in existing if item.get("id") != watchlist_id]
    if len(remaining) == len(existing):
        return None
    deleted = next((item for item in existing if item.get("id") == watchlist_id), None)
    _save_all(remaining)
    return deleted
