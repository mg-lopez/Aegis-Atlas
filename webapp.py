"""Hackathon dashboard server for Aegis Atlas."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timedelta, timezone
from math import cos, radians
from typing import Any

from flask import Flask, jsonify, render_template, request

from agent_skeleton import run_pipeline
from history_store import append_history, read_recent_history
from notifications import notify_alert
from watchlists import create_watchlist, get_watchlist, list_watchlists

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

PIPELINE_TIMEOUT_SECONDS = int(os.getenv("AEGIS_PIPELINE_TIMEOUT_SECONDS", "75"))
LIVE_FAST_MODE_DEFAULT = os.getenv("AEGIS_LIVE_FAST_MODE", "1") == "1"
_PIPELINE_EXECUTOR = ThreadPoolExecutor(max_workers=4)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _point_to_bbox(lat: float, lon: float, km_radius: float = 25.0) -> list[float]:
    """Convert a point into a small AOI bbox around it."""
    lat_delta = km_radius / 111.0
    cos_lat = max(0.1, cos(radians(lat)))
    lon_delta = km_radius / (111.0 * cos_lat)

    min_lon = _clamp(lon - lon_delta, -180.0, 180.0)
    min_lat = _clamp(lat - lat_delta, -90.0, 90.0)
    max_lon = _clamp(lon + lon_delta, -180.0, 180.0)
    max_lat = _clamp(lat + lat_delta, -90.0, 90.0)
    return [min_lon, min_lat, max_lon, max_lat]


def _confidence_from_score(score: float | None, threat_level: str) -> str:
    if score is None:
        return "low"
    if threat_level == "high":
        return "high"
    if threat_level == "medium":
        return "medium"
    return "medium" if score >= 0.2 else "low"


def _parse_float(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"Missing required field: {key}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {key}") from exc


def _parse_member(member: dict[str, Any]) -> dict[str, Any]:
    lat = _clamp(_parse_float(member, "lat"), -90.0, 90.0)
    lon = _clamp(_parse_float(member, "lon"), -180.0, 180.0)
    label = str(member.get("label", f"{lat:.4f},{lon:.4f}")).strip()
    if not label:
        label = f"{lat:.4f},{lon:.4f}"
    if len(label) > 80:
        label = label[:80]
    return {"label": label, "lat": lat, "lon": lon}


def _normalize_alert_response(
    alert: dict[str, Any],
    lat: float,
    lon: float,
    bbox: list[float],
    start_date: str,
    end_date: str,
    mode: str,
) -> dict[str, Any]:
    threat_level = str(alert.get("threat_level", "none"))
    score = alert.get("score")
    alert_confidence = alert.get("confidence")
    return {
        "ok": True,
        "mode": mode,
        "query": {
            "lat": lat,
            "lon": lon,
            "bbox": bbox,
            "start_date": start_date,
            "end_date": end_date,
        },
        "threat_level": threat_level,
        "score": score,
        "confidence": (
            str(alert_confidence)
            if isinstance(alert_confidence, str)
            else _confidence_from_score(score if isinstance(score, (int, float)) else None, threat_level)
        ),
        "confidence_score": alert.get("confidence_score"),
        "recommended_action": alert.get("recommended_action", "No recommendation available."),
        "sources": alert.get("sources", []),
        "rationale": alert.get("rationale", []),
        "explainability": alert.get("explainability", {}),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def _run_pipeline_with_timeout(
    bbox: list[float],
    start_date: str,
    end_date: str,
    use_sample: bool,
    use_live_fast: bool = False,
) -> dict[str, Any]:
    future = _PIPELINE_EXECUTOR.submit(
        run_pipeline,
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        use_sample=use_sample,
        use_live_fast=use_live_fast,
    )
    try:
        return future.result(timeout=PIPELINE_TIMEOUT_SECONDS)
    except FuturesTimeoutError as exc:
        raise TimeoutError(
            f"Analysis timed out after {PIPELINE_TIMEOUT_SECONDS}s in {'sample' if use_sample else 'live'} mode."
        ) from exc


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.post("/api/analyze")
def analyze_location() -> Any:
    payload = request.get_json(silent=True) or {}

    try:
        lat = _parse_float(payload, "lat")
        lon = _parse_float(payload, "lon")
        lat = _clamp(lat, -90.0, 90.0)
        lon = _clamp(lon, -180.0, 180.0)
    except ValueError as exc:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": str(exc),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
            ),
            400,
        )

    mode = str(payload.get("mode", "sample")).lower()
    use_sample = mode != "live"
    response_mode = "sample" if use_sample else "live"
    deep_live = bool(payload.get("deep_live", False))
    use_live_fast = (response_mode == "live") and LIVE_FAST_MODE_DEFAULT and (not deep_live)

    now = datetime.now(timezone.utc).date()
    start_date = str(payload.get("start_date", (now - timedelta(days=30)).isoformat()))
    end_date = str(payload.get("end_date", now.isoformat()))

    bbox = _point_to_bbox(lat, lon, km_radius=25.0)

    app.logger.info(
        "Analyze request started: mode=%s lat=%.5f lon=%.5f start=%s end=%s",
        response_mode,
        lat,
        lon,
        start_date,
        end_date,
    )

    try:
        alert = _run_pipeline_with_timeout(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            use_sample=use_sample,
            use_live_fast=use_live_fast,
        )
    except TimeoutError as exc:
        app.logger.warning("Analyze request timeout: %s", exc)
        return (
            jsonify(
                {
                    "ok": False,
                    "error": str(exc),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
            ),
            504,
        )
    except Exception as exc:  # pragma: no cover
        app.logger.exception("Analyze request failed")
        return (
            jsonify(
                {
                    "ok": False,
                    "error": str(exc),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )

    response = _normalize_alert_response(
        alert=alert,
        lat=lat,
        lon=lon,
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        mode=response_mode,
    )

    notify_cfg = payload.get("notify") if isinstance(payload.get("notify"), dict) else {}
    notifications = notify_alert(
        response,
        webhook_url=str(notify_cfg.get("webhook_url", "")).strip() or None,
        email_to=str(notify_cfg.get("email_to", "")).strip() or None,
    )
    response["notifications"] = notifications

    history_entry = append_history(
        {
            "type": "single_analysis",
            "mode": response_mode,
            "query": response["query"],
            "alert": {
                "threat_level": response["threat_level"],
                "score": response["score"],
                "confidence": response["confidence"],
                "recommended_action": response["recommended_action"],
            },
            "notifications": notifications,
        }
    )
    response["history_id"] = history_entry["id"]
    app.logger.info(
        "Analyze request completed: mode=%s threat=%s score=%s",
        response_mode,
        response["threat_level"],
        response["score"],
    )
    return jsonify(response)


@app.get("/api/history")
def get_history() -> Any:
    limit_raw = request.args.get("limit", "20")
    try:
        limit = max(1, min(200, int(limit_raw)))
    except ValueError:
        limit = 20
    return jsonify({"ok": True, "items": read_recent_history(limit=limit)})


@app.get("/api/watchlists")
def get_watchlists() -> Any:
    return jsonify({"ok": True, "items": list_watchlists()})


@app.post("/api/watchlists")
def post_watchlist() -> Any:
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip() or "Family Watchlist"
    members_raw = payload.get("members")
    if not isinstance(members_raw, list) or not members_raw:
        return jsonify({"ok": False, "error": "members must be a non-empty array"}), 400
    if len(members_raw) > 25:
        return jsonify({"ok": False, "error": "members cannot exceed 25 locations"}), 400
    try:
        members = [_parse_member(m) for m in members_raw if isinstance(m, dict)]
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    if not members:
        return jsonify({"ok": False, "error": "No valid members provided"}), 400
    created = create_watchlist(name=name, members=members)
    return jsonify({"ok": True, "watchlist": created}), 201


@app.post("/api/watchlists/<watchlist_id>/scan")
def scan_watchlist(watchlist_id: str) -> Any:
    watchlist = get_watchlist(watchlist_id)
    if watchlist is None:
        return jsonify({"ok": False, "error": "watchlist not found"}), 404

    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "sample")).lower()
    use_sample = mode != "live"
    response_mode = "sample" if use_sample else "live"
    deep_live = bool(payload.get("deep_live", False))
    use_live_fast = (response_mode == "live") and LIVE_FAST_MODE_DEFAULT and (not deep_live)

    now = datetime.now(timezone.utc).date()
    start_date = str(payload.get("start_date", (now - timedelta(days=30)).isoformat()))
    end_date = str(payload.get("end_date", now.isoformat()))

    notify_cfg = payload.get("notify") if isinstance(payload.get("notify"), dict) else {}
    results: list[dict[str, Any]] = []
    for member in watchlist.get("members", []):
        lat = float(member["lat"])
        lon = float(member["lon"])
        bbox = _point_to_bbox(lat, lon, km_radius=25.0)
        try:
            alert = _run_pipeline_with_timeout(
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                use_sample=use_sample,
                use_live_fast=use_live_fast,
            )
            response = _normalize_alert_response(
                alert=alert,
                lat=lat,
                lon=lon,
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                mode=response_mode,
            )
            response["member_label"] = str(member.get("label", "member"))
            response["notifications"] = notify_alert(
                response,
                webhook_url=str(notify_cfg.get("webhook_url", "")).strip() or None,
                email_to=str(notify_cfg.get("email_to", "")).strip() or None,
            )
            results.append(response)
        except Exception as exc:  # pragma: no cover
            results.append(
                {
                    "ok": False,
                    "member_label": str(member.get("label", "member")),
                    "query": {
                        "lat": lat,
                        "lon": lon,
                        "bbox": bbox,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                    "error": str(exc),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
            )

    history_entry = append_history(
        {
            "type": "watchlist_scan",
            "watchlist_id": watchlist_id,
            "mode": response_mode,
            "result_count": len(results),
            "results": [
                {
                    "member_label": r.get("member_label"),
                    "threat_level": r.get("threat_level", "error"),
                    "score": r.get("score"),
                    "confidence": r.get("confidence"),
                    "ok": bool(r.get("ok", False)),
                }
                for r in results
            ],
        }
    )

    return jsonify(
        {
            "ok": True,
            "watchlist": {"id": watchlist.get("id"), "name": watchlist.get("name")},
            "results": results,
            "history_id": history_entry["id"],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
