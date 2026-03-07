"""Hackathon dashboard server for Aegis Atlas."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timedelta, timezone
from math import cos, radians
from typing import Any

from flask import Flask, jsonify, render_template, request

from agent_skeleton import RISK_PROFILES, run_pipeline
from history_store import append_history, read_all_history, read_history_by_id, read_recent_history
from incident_store import (
    close_incident,
    create_incident,
    find_open_incident_by_analysis_key,
    get_incident,
    list_incidents,
    update_incident,
)
from lens_profiles import available_lenses, lens_recommended_action, resolve_lens, score_signals_for_lens
from notifications import notify_alert
from risk_intel import list_instability_zones
from trend_intel import (
    build_analysis_key,
    build_single_analysis_trend_points,
    build_trend_summary,
    build_watchlist_trend_summary,
)
from watchlists import create_watchlist, delete_watchlist, get_watchlist, list_watchlists, update_watchlist_alerts

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

PIPELINE_TIMEOUT_SECONDS = int(os.getenv("AEGIS_PIPELINE_TIMEOUT_SECONDS", "75"))
LIVE_FAST_MODE_DEFAULT = os.getenv("AEGIS_LIVE_FAST_MODE", "1") == "1"
_PIPELINE_EXECUTOR = ThreadPoolExecutor(max_workers=4)
VALID_RISK_PROFILES = {"conservative", "balanced", "sensitive"}
THREAT_PRIORITY = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0}
ANALYSIS_PRESETS = [
    {
        "id": "red-sea-corridor",
        "name": "Red Sea Corridor",
        "region": "Bab-el-Mandeb",
        "description": "Strategic chokepoint watch for logistics and shipping exposure.",
        "demo_headline": "Shipping exposure is concentrated around a commercially sensitive corridor with immediate customer relevance.",
        "operator_note": "Best opening scenario for paid logistics and security storytelling.",
        "lat": 12.6729,
        "lon": 43.4214,
        "radius_km": 55.0,
        "mode": "live",
        "risk_profile": "balanced",
        "lens": "logistics",
        "threat_level": "high",
        "priority": 100,
        "featured": True,
        "watchlist_name": "Red Sea Assets",
        "watchlist_seed": [
            {"label": "Bab-el-Mandeb Lane", "lat": 12.6450, "lon": 43.4100},
            {"label": "Aden Anchorage", "lat": 12.7850, "lon": 45.0180},
            {"label": "Djibouti Port", "lat": 11.5945, "lon": 43.1480},
        ],
    },
    {
        "id": "gaza-conflict",
        "name": "Gaza Conflict Lens",
        "region": "Gaza Strip",
        "description": "Conflict-heavy AOI for geo-political corroboration and alert tuning.",
        "demo_headline": "Escalation posture, access disruption, and strike-risk context align into a strong security demo narrative.",
        "operator_note": "Best scenario for security, humanitarian, and instability-led demos.",
        "lat": 31.4432,
        "lon": 34.3600,
        "radius_km": 32.0,
        "mode": "live",
        "risk_profile": "sensitive",
        "lens": "security",
        "threat_level": "critical",
        "priority": 95,
        "watchlist_name": "Gaza Priority Sites",
        "watchlist_seed": [
            {"label": "Crossing Node", "lat": 31.5340, "lon": 34.4870},
            {"label": "Coastal Access Route", "lat": 31.4670, "lon": 34.3980},
            {"label": "Southern Corridor", "lat": 31.3430, "lon": 34.2910},
        ],
    },
    {
        "id": "sendai-seismic",
        "name": "Sendai Seismic Watch",
        "region": "Miyagi, Japan",
        "description": "Earthquake-oriented live scan around the Sendai corridor.",
        "demo_headline": "A clean insurance and continuity scenario for severity framing, recurrence watch, and customer exposure language.",
        "operator_note": "Best scenario for insurance and continuity buyers.",
        "lat": 38.2682,
        "lon": 140.8694,
        "radius_km": 40.0,
        "mode": "live",
        "risk_profile": "sensitive",
        "lens": "insurance",
        "threat_level": "high",
        "priority": 88,
        "watchlist_name": "Sendai Exposure Set",
        "watchlist_seed": [
            {"label": "Industrial Port", "lat": 38.2560, "lon": 141.0110},
            {"label": "Inland Distribution", "lat": 38.2450, "lon": 140.9250},
            {"label": "Utility Corridor", "lat": 38.3130, "lon": 140.9780},
        ],
    },
    {
        "id": "napa-wildfire-demo",
        "name": "Napa Wildfire Demo",
        "region": "California, USA",
        "description": "Deterministic sample-mode wildfire storyline for polished demos.",
        "demo_headline": "A deterministic sample storyline for safe fallback demos when live corroboration is unavailable.",
        "operator_note": "Best backup scenario when a deterministic sample is needed.",
        "lat": 38.4404,
        "lon": -122.7141,
        "radius_km": 28.0,
        "mode": "sample",
        "risk_profile": "balanced",
        "lens": "general",
        "threat_level": "medium",
        "priority": 70,
        "watchlist_name": "Napa Demo Assets",
        "watchlist_seed": [
            {"label": "Vineyard Cluster", "lat": 38.4740, "lon": -122.7290},
            {"label": "North Access Road", "lat": 38.5120, "lon": -122.6950},
        ],
    },
]


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
    if threat_level == "critical":
        return "high"
    if threat_level == "high":
        return "high"
    if threat_level == "medium":
        return "medium"
    return "medium" if score >= 0.2 else "low"


def _threat_level_from_score(score: float | None, risk_profile: str) -> str:
    if score is None:
        return "none"
    profile = RISK_PROFILES.get(str(risk_profile).lower(), RISK_PROFILES["balanced"])
    if score >= profile.critical_threshold:
        return "critical"
    if score >= profile.high_threshold:
        return "high"
    if score >= profile.medium_threshold:
        return "medium"
    return "low"


def _parse_float(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"Missing required field: {key}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {key}") from exc


def _parse_bool(payload: dict[str, Any], key: str, default: bool = False) -> bool:
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def _parse_radius_km(payload: dict[str, Any]) -> float:
    raw = payload.get("radius_km", 25.0)
    try:
        radius = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid numeric value for radius_km") from exc
    return _clamp(radius, 5.0, 250.0)


def _parse_lens(payload: dict[str, Any]) -> str:
    lens = resolve_lens(payload.get("lens"))
    return lens.id


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
    risk_profile: str,
    lens: str,
    radius_km: float,
    deep_live: bool,
) -> dict[str, Any]:
    threat_level = str(alert.get("threat_level", "none"))
    score = alert.get("score")
    alert_confidence = alert.get("confidence")
    response = {
        "ok": True,
        "mode": mode,
        "risk_profile": str(alert.get("risk_profile", risk_profile)),
        "query": {
            "lat": lat,
            "lon": lon,
            "bbox": bbox,
            "start_date": start_date,
            "end_date": end_date,
            "risk_profile": risk_profile,
            "lens": lens,
            "radius_km": radius_km,
            "deep_live": deep_live,
        },
        "threat_level": threat_level,
        "score": score,
        "score_label": str(alert.get("score_label", threat_level)),
        "confidence": (
            str(alert_confidence)
            if isinstance(alert_confidence, str)
            else _confidence_from_score(score if isinstance(score, (int, float)) else None, threat_level)
        ),
        "confidence_score": alert.get("confidence_score"),
        "recommended_action": alert.get("recommended_action", "No recommendation available."),
        "sources": alert.get("sources", []),
        "source_details": alert.get("source_details", []),
        "rationale": alert.get("rationale", []),
        "explainability": alert.get("explainability", {}),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    response = _apply_customer_lens(response)
    response["evidence_health"] = _build_evidence_health(response)
    response["brief"] = _build_mission_brief(response)
    return response


def _analysis_key_from_query(
    *,
    lat: float,
    lon: float,
    radius_km: float,
    mode: str,
    risk_profile: str,
    lens: str,
    deep_live: bool,
) -> str:
    return build_analysis_key(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        mode=mode,
        risk_profile=risk_profile,
        lens=lens,
        deep_live=deep_live,
    )


def _dominant_signal_key(payload: dict[str, Any]) -> str | None:
    dominant_signal = payload.get("brief", {}).get("dominant_signal", {})
    if not isinstance(dominant_signal, dict):
        return None
    key = dominant_signal.get("key")
    return str(key) if key else None


def _brief_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    brief = payload.get("brief", {})
    dominant_signal = brief.get("dominant_signal", {}) if isinstance(brief.get("dominant_signal"), dict) else {}
    return {
        "headline": brief.get("headline"),
        "quality_band": brief.get("quality_band"),
        "analysis_mode_label": brief.get("analysis_mode_label"),
        "lens_label": brief.get("lens_label"),
        "dominant_signal_label": dominant_signal.get("label"),
        "dominant_signal_key": dominant_signal.get("key"),
    }


def _analysis_export_payload(response: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "analysis_brief",
        "generated_at": response.get("last_updated"),
        "history_id": response.get("history_id"),
        "query": response.get("query", {}),
        "threat_level": response.get("threat_level"),
        "score": response.get("score"),
        "score_label": response.get("score_label"),
        "confidence": response.get("confidence"),
        "confidence_score": response.get("confidence_score"),
        "risk_profile": response.get("risk_profile"),
        "lens": response.get("lens"),
        "lens_label": response.get("lens_label"),
        "recommended_action": response.get("recommended_action"),
        "brief": response.get("brief", {}),
        "trend": response.get("trend"),
        "sources": response.get("sources", []),
        "source_details": response.get("source_details", []),
        "rationale": response.get("rationale", []),
        "explainability": response.get("explainability", {}),
        "lens_explainability": response.get("lens_explainability", {}),
        "lens_insight": response.get("lens_insight"),
        "incident_context": response.get("incident_context"),
        "evidence_health": response.get("evidence_health", {}),
    }


def _watchlist_export_payload(
    *,
    watchlist: dict[str, Any],
    summary: dict[str, Any],
    results: list[dict[str, Any]],
    mode: str,
    lens: str,
) -> dict[str, Any]:
    top_results = sorted(
        [item for item in results if item.get("ok") is True],
        key=lambda item: (
            THREAT_PRIORITY.get(str(item.get("threat_level", "none")), 0),
            float(item.get("score") or 0.0),
        ),
        reverse=True,
    )[:5]
    return {
        "type": "watchlist_brief",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "watchlist": {"id": watchlist.get("id"), "name": watchlist.get("name")},
        "mode": mode,
        "lens": lens,
        "lens_label": summary.get("lens_label"),
        "summary": summary,
        "results": results,
        "top_results": top_results,
        "analytics_snapshot": _watchlist_analytics_snapshot(summary, results, mode=mode, lens=lens),
        "recent_bulletins": _build_bulletins(lens, limit=4),
        "alert_subscription": _normalize_watchlist_alerts(watchlist.get("alerts")),
    }


def _normalize_watchlist_alerts(raw_alerts: Any) -> dict[str, Any]:
    alerts = raw_alerts if isinstance(raw_alerts, dict) else {}
    email_to = str(alerts.get("email_to", "")).strip()
    sms_to = str(alerts.get("sms_to", "")).strip()
    threshold = str(alerts.get("threshold", "high")).strip().lower()
    if threshold not in {"medium", "high", "critical"}:
        threshold = "high"
    return {
        "email_enabled": bool(alerts.get("email_enabled", email_to)),
        "sms_enabled": bool(alerts.get("sms_enabled", False) and sms_to),
        "email_to": email_to,
        "sms_to": sms_to,
        "threshold": threshold,
        "updated_at": alerts.get("updated_at"),
    }


def _watchlist_analytics_snapshot(
    summary: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    mode: str,
    lens: str,
) -> dict[str, Any]:
    ok_results = [item for item in results if item.get("ok") is True]
    highest = next(
        (
            item for item in sorted(
                ok_results,
                key=lambda item: (
                    THREAT_PRIORITY.get(str(item.get("threat_level", "none")), 0),
                    float(item.get("score") or 0.0),
                ),
                reverse=True,
            )
        ),
        None,
    )
    counts = {
        level: sum(1 for item in ok_results if str(item.get("threat_level", "none")).lower() == level)
        for level in ("critical", "high", "medium", "low", "none")
    }
    return {
        "mode": mode,
        "lens": lens,
        "scanned_locations": len(ok_results),
        "high_or_above": counts["critical"] + counts["high"],
        "medium_or_above": counts["critical"] + counts["high"] + counts["medium"],
        "average_score": summary.get("average_score"),
        "top_hotspot": summary.get("top_hotspot"),
        "highest_result": highest,
    }


def _build_watchlist_alert_package(
    *,
    watchlist: dict[str, Any],
    summary: dict[str, Any],
    results: list[dict[str, Any]],
    mode: str,
    lens: str,
    triggered_result: dict[str, Any],
) -> dict[str, str]:
    export_payload = _watchlist_export_payload(
        watchlist=watchlist,
        summary=summary,
        results=results,
        mode=mode,
        lens=lens,
    )
    export_payload["alert_trigger"] = {
        "member_label": triggered_result.get("member_label"),
        "threat_level": triggered_result.get("threat_level"),
        "score": triggered_result.get("score"),
        "confidence": triggered_result.get("confidence"),
        "recommended_action": triggered_result.get("recommended_action"),
    }
    html_body = render_template(
        "watchlist_brief.html",
        export=export_payload,
        history={"id": "alert-digest"},
    )
    analytics = export_payload.get("analytics_snapshot", {})
    bulletins = export_payload.get("recent_bulletins", [])[:3]
    text_lines = [
        f"Watchlist: {watchlist.get('name') or 'Watchlist'}",
        f"Triggered member: {triggered_result.get('member_label') or 'Unknown'}",
        f"Threat level: {str(triggered_result.get('threat_level', 'unknown')).upper()}",
        f"Score: {triggered_result.get('score')}",
        f"Confidence: {triggered_result.get('confidence')}",
        f"Recommended action: {triggered_result.get('recommended_action') or 'No recommendation available.'}",
        "",
        f"Scanned locations: {analytics.get('scanned_locations', len(results))}",
        f"High or above: {analytics.get('high_or_above', 0)}",
        f"Average score: {analytics.get('average_score')}",
    ]
    if bulletins:
        text_lines.append("")
        text_lines.append("Relevant bulletins:")
        text_lines.extend(f"- {item.get('title')}: {item.get('summary')}" for item in bulletins)
    sms_message = (
        f"Aegis Atlas {str(triggered_result.get('threat_level', 'unknown')).upper()} "
        f"alert for {triggered_result.get('member_label') or watchlist.get('name')}. "
        f"{triggered_result.get('recommended_action') or 'Review the latest dashboard brief.'}"
    )
    return {
        "html_body": html_body,
        "text_body": "\n".join(text_lines).strip(),
        "sms_message": sms_message,
    }


def _normalize_export_record(history_record: dict[str, Any]) -> dict[str, Any]:
    record_type = str(history_record.get("type", ""))
    if record_type == "single_analysis":
        export_payload = history_record.get("export_payload")
        if isinstance(export_payload, dict):
            normalized = dict(export_payload)
            normalized["history_id"] = normalized.get("history_id") or history_record.get("id")
            return normalized
        query = history_record.get("query", {})
        alert = history_record.get("alert", {})
        brief = history_record.get("brief", {})
        return {
            "type": "analysis_brief",
            "generated_at": history_record.get("created_at"),
            "history_id": history_record.get("id"),
            "query": query,
            "threat_level": alert.get("threat_level"),
            "score": alert.get("score"),
            "score_label": alert.get("threat_level"),
            "confidence": alert.get("confidence"),
            "risk_profile": query.get("risk_profile"),
            "lens": query.get("lens", history_record.get("lens", "general")),
            "lens_label": brief.get("lens_label"),
            "recommended_action": alert.get("recommended_action"),
            "brief": brief,
            "trend": None,
            "sources": [],
            "source_details": [],
            "rationale": [],
            "explainability": {},
            "lens_explainability": {},
            "evidence_health": {},
        }
    if record_type == "watchlist_scan":
        export_payload = history_record.get("export_payload")
        if isinstance(export_payload, dict):
            normalized = dict(export_payload)
            normalized["history_id"] = normalized.get("history_id") or history_record.get("id")
            return normalized
        return {
            "type": "watchlist_brief",
            "generated_at": history_record.get("created_at"),
            "history_id": history_record.get("id"),
            "watchlist": {"id": history_record.get("watchlist_id"), "name": None},
            "mode": history_record.get("mode"),
            "lens": history_record.get("lens", "general"),
            "lens_label": history_record.get("summary", {}).get("lens_label"),
            "summary": history_record.get("summary", {}),
            "results": history_record.get("results", []),
            "top_results": history_record.get("results", [])[:5],
        }
    raise ValueError("Unsupported history record type")


def _render_export_html(history_record: dict[str, Any], export_payload: dict[str, Any]) -> str:
    if export_payload.get("type") == "analysis_brief":
        return render_template(
            "analysis_brief.html",
            export=export_payload,
            history=history_record,
        )
    if export_payload.get("type") == "watchlist_brief":
        return render_template(
            "watchlist_brief.html",
            export=export_payload,
            history=history_record,
        )
    raise ValueError("Unsupported export payload type")


def _signal_display_name(signal_key: str) -> str:
    return signal_key.replace("_", " ").replace("-", " ").title()


def _dominant_signal(payload: dict[str, Any]) -> dict[str, Any] | None:
    lens_dominant = payload.get("lens_explainability", {}).get("dominant_signal")
    if isinstance(lens_dominant, dict) and lens_dominant:
        return lens_dominant
    signals = payload.get("explainability", {}).get("signals", [])
    if not isinstance(signals, list) or not signals:
        return None
    ranked = sorted(
        [signal for signal in signals if isinstance(signal, dict)],
        key=lambda signal: (
            float(signal.get("contribution") or 0.0) * float(signal.get("reliability") or 0.5),
            float(signal.get("score") or 0.0),
        ),
        reverse=True,
    )
    if not ranked:
        return None
    top = ranked[0]
    return {
        "key": str(top.get("key", "unknown")),
        "label": _signal_display_name(str(top.get("key", "unknown"))),
        "hazard_type": str(top.get("hazard_type", "unknown")),
        "status": str(top.get("status", "unknown")),
        "score": top.get("score"),
        "details": str(top.get("details", "")),
        "source": str(top.get("source", "")),
    }


def _apply_customer_lens(response: dict[str, Any]) -> dict[str, Any]:
    lens = resolve_lens(response.get("query", {}).get("lens"))
    signals = response.get("explainability", {}).get("signals", [])
    base_score = response.get("score")
    lens_score, weighted_signals, dominant_signal = score_signals_for_lens(signals, lens, base_score)
    dominant_signal_payload = None
    if isinstance(dominant_signal, dict):
        dominant_signal_payload = {
            "key": str(dominant_signal.get("key", "unknown")),
            "label": _signal_display_name(str(dominant_signal.get("key", "unknown"))),
            "hazard_type": str(dominant_signal.get("hazard_type", "unknown")),
            "status": str(dominant_signal.get("status", "unknown")),
            "score": dominant_signal.get("score"),
            "details": str(dominant_signal.get("details", "")),
            "source": str(dominant_signal.get("source", "")),
        }

    response["lens"] = lens.id
    response["lens_label"] = lens.label
    response["lens_summary"] = lens.description
    response["base_assessment"] = {
        "score": response.get("score"),
        "threat_level": response.get("threat_level"),
        "score_label": response.get("score_label"),
        "recommended_action": response.get("recommended_action"),
    }
    response["score"] = lens_score
    response["threat_level"] = _threat_level_from_score(lens_score, str(response.get("risk_profile", "balanced")))
    response["score_label"] = response["threat_level"]
    response["recommended_action"] = lens_recommended_action(lens, str(response["threat_level"]))
    response["confidence"] = str(
        response.get("confidence")
        or _confidence_from_score(lens_score if isinstance(lens_score, (int, float)) else None, response["threat_level"])
    )
    response["lens_explainability"] = {
        "lens": lens.id,
        "label": lens.label,
        "description": lens.description,
        "weighted_signals": weighted_signals,
        "dominant_signal": dominant_signal_payload,
    }
    response["rationale"] = list(response.get("rationale", [])) + [
        f"{lens.label} lens prioritizes {lens.watchlist_focus.lower()}"
    ]
    return response


def _quality_band(coverage: float, consensus: float, confidence_score: float) -> str:
    blended = (0.40 * coverage) + (0.25 * consensus) + (0.35 * confidence_score)
    if blended >= 0.72:
        return "strong"
    if blended >= 0.48:
        return "moderate"
    return "limited"


def _source_health_summary(payload: dict[str, Any]) -> dict[str, Any]:
    signals = payload.get("explainability", {}).get("signals", [])
    counts = {"ok": 0, "no_event": 0, "insufficient_data": 0, "unavailable": 0, "other": 0}
    for signal in signals:
        if not isinstance(signal, dict):
            continue
        status = str(signal.get("status", "other"))
        counts[status if status in counts else "other"] += 1
    return counts


def _parse_iso_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(f"{text}T00:00:00+00:00")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _freshness_label_from_hours(hours: float | None) -> tuple[str, str]:
    if hours is None:
        return "unknown", "No acquisition timestamp is available for the returned scenes."
    if hours <= 72:
        return "fresh", f"Latest satellite acquisition is {hours:.0f} hours old."
    if hours <= 168:
        return "aging", f"Latest satellite acquisition is {hours:.0f} hours old."
    return "stale", f"Latest satellite acquisition is {hours:.0f} hours old."


def _strength_label(value: float) -> str:
    if value >= 0.75:
        return "strong"
    if value >= 0.45:
        return "moderate"
    return "limited"


def _satellite_health_summary(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload.get("query", {})
    mode = str(payload.get("mode", "sample"))
    signals = payload.get("explainability", {}).get("signals", [])
    sat_signal = next(
        (
            signal
            for signal in signals
            if isinstance(signal, dict) and str(signal.get("key", "")).strip() == "sentinel_change"
        ),
        None,
    )
    source_details = payload.get("source_details", [])

    latest_scene_at: datetime | None = None
    for item in source_details if isinstance(source_details, list) else []:
        if not isinstance(item, dict):
            continue
        parsed = _parse_iso_datetime(item.get("datetime"))
        if parsed is not None and (latest_scene_at is None or parsed > latest_scene_at):
            latest_scene_at = parsed

    if mode == "sample":
        return {
            "label": "demo",
            "status": "sample",
            "observed_at": latest_scene_at.isoformat() if latest_scene_at is not None else None,
            "freshness_hours": None,
            "source": "sample-assets",
            "summary": "Sample mode is using deterministic demo imagery rather than a current acquisition.",
            "mode_label": "Sample imagery",
        }

    if not isinstance(sat_signal, dict):
        return {
            "label": "unknown",
            "status": "unknown",
            "observed_at": latest_scene_at.isoformat() if latest_scene_at is not None else None,
            "freshness_hours": None,
            "source": None,
            "summary": "Satellite signal metadata was not returned.",
            "mode_label": "Unknown",
        }

    sat_status = str(sat_signal.get("status", "unknown"))
    sat_source = str(sat_signal.get("source", "sentinel-2"))
    is_proxy = sat_source == "sentinel-2-stac-meta"

    if sat_status == "unavailable":
        return {
            "label": "unavailable",
            "status": sat_status,
            "observed_at": latest_scene_at.isoformat() if latest_scene_at is not None else None,
            "freshness_hours": None,
            "source": sat_source,
            "summary": str(sat_signal.get("details", "Satellite evidence unavailable.")),
            "mode_label": "Unavailable",
        }
    if sat_status == "insufficient_data":
        return {
            "label": "partial",
            "status": sat_status,
            "observed_at": latest_scene_at.isoformat() if latest_scene_at is not None else None,
            "freshness_hours": None,
            "source": sat_source,
            "summary": str(sat_signal.get("details", "Satellite evidence is only partially available.")),
            "mode_label": "Partial imagery",
        }

    freshness_hours = None
    freshness_label = "unknown"
    freshness_summary = "No acquisition timestamp is available for the returned scenes."
    if latest_scene_at is not None:
        freshness_hours = max(0.0, (datetime.now(timezone.utc) - latest_scene_at).total_seconds() / 3600.0)
        freshness_label, freshness_summary = _freshness_label_from_hours(freshness_hours)

    mode_label = "Fast scout proxy" if is_proxy else "Scene-delta imagery"
    if is_proxy:
        freshness_summary = f"{freshness_summary} Fast scout is using STAC metadata rather than a full scene comparison."

    return {
        "label": freshness_label,
        "status": sat_status,
        "observed_at": latest_scene_at.isoformat() if latest_scene_at is not None else None,
        "freshness_hours": round(freshness_hours, 1) if freshness_hours is not None else None,
        "source": sat_source,
        "summary": freshness_summary,
        "mode_label": mode_label,
    }


def _external_feed_health_summary(payload: dict[str, Any]) -> dict[str, Any]:
    signals = payload.get("explainability", {}).get("signals", [])
    external_signals = [
        signal
        for signal in signals
        if isinstance(signal, dict) and str(signal.get("key", "")).strip() != "sentinel_change"
    ]
    if not external_signals:
        return {
            "label": "limited",
            "summary": "No external feeds were included in the explainability payload.",
            "healthy_count": 0,
            "degraded_count": 0,
            "unavailable_count": 0,
            "total_count": 0,
        }

    healthy_count = 0
    degraded_count = 0
    unavailable_count = 0
    for signal in external_signals:
        status = str(signal.get("status", "unknown"))
        if status in {"ok", "no_event"}:
            healthy_count += 1
        elif status == "insufficient_data":
            degraded_count += 1
        elif status == "unavailable":
            unavailable_count += 1
        else:
            degraded_count += 1

    if unavailable_count == len(external_signals):
        label = "offline"
    elif degraded_count + unavailable_count > 0:
        label = "partial"
    else:
        label = "healthy"

    summary = (
        f"{healthy_count} of {len(external_signals)} external feeds are healthy; "
        f"{degraded_count} degraded, {unavailable_count} unavailable."
    )
    return {
        "label": label,
        "summary": summary,
        "healthy_count": healthy_count,
        "degraded_count": degraded_count,
        "unavailable_count": unavailable_count,
        "total_count": len(external_signals),
    }


def _build_evidence_health(payload: dict[str, Any]) -> dict[str, Any]:
    explainability = payload.get("explainability", {})
    coverage = float(explainability.get("coverage", 0.0) or 0.0)
    consensus = float(explainability.get("consensus", 0.0) or 0.0)
    confidence_score = float(payload.get("confidence_score", 0.0) or 0.0)
    quality_band = _quality_band(coverage, consensus, confidence_score)
    satellite = _satellite_health_summary(payload)
    external_feeds = _external_feed_health_summary(payload)
    notes: list[str] = []

    if payload.get("mode") == "sample":
        notes.append("Sample mode is useful for demos but should not be presented as current operational evidence.")
    elif not payload.get("query", {}).get("deep_live"):
        notes.append("Live Fast mode uses a quicker STAC scout path and can understate or proxy satellite evidence.")

    if satellite["label"] in {"stale", "unavailable", "partial"}:
        notes.append(str(satellite.get("summary", "")).strip())
    if external_feeds["label"] in {"partial", "offline", "limited"}:
        notes.append(str(external_feeds.get("summary", "")).strip())
    if quality_band == "limited":
        notes.append("Coverage or consensus is limited, so this result should be treated as a lead rather than fully corroborated evidence.")

    deduped_notes = [note for note in dict.fromkeys(note for note in notes if note)]

    if payload.get("mode") == "sample":
        overall_label = "demo"
        summary = "Evidence is presentation-friendly but based on demo/sample assets."
    elif satellite["label"] in {"unavailable", "partial"} or external_feeds["label"] == "offline":
        overall_label = "degraded"
        summary = "Evidence health is degraded because key satellite or feed inputs are unavailable."
    elif quality_band == "limited" or satellite["label"] == "stale" or external_feeds["label"] == "partial":
        overall_label = "watch"
        summary = "Evidence is usable, but freshness or corroboration is only partial."
    else:
        overall_label = "healthy"
        summary = "Evidence is fresh and corroborated enough for customer-facing use."

    return {
        "overall_label": overall_label,
        "summary": summary,
        "quality_band": quality_band,
        "coverage": {"value": round(coverage, 4), "label": _strength_label(coverage)},
        "consensus": {"value": round(consensus, 4), "label": _strength_label(consensus)},
        "satellite": satellite,
        "external_feeds": external_feeds,
        "source_health": _source_health_summary(payload),
        "notes": deduped_notes[:4],
    }


def _build_customer_tags(payload: dict[str, Any], dominant_signal: dict[str, Any] | None) -> list[str]:
    tags: list[str] = []
    lens = resolve_lens(payload.get("lens"))
    threat_level = str(payload.get("threat_level", "none"))
    if threat_level in {"critical", "high"}:
        tags.append("Immediate Ops Risk")
    elif threat_level == "medium":
        tags.append("Escalation Watch")
    else:
        tags.append("Monitor Mode")

    if payload.get("mode") == "live":
        tags.append("Live Scan")
    else:
        tags.append("Demo Proof")
    tags.append(lens.customer_tag)

    query = payload.get("query", {})
    radius = query.get("radius_km")
    if isinstance(radius, (int, float)):
        tags.append(f"{float(radius):.0f} km AOI")

    if dominant_signal:
        hazard = dominant_signal.get("hazard_type", "")
        if hazard in {"geopolitical", "geopolitical-composite", "drone-missile"}:
            tags.append("Security Exposure")
        elif hazard in {"earthquake", "global-alert"}:
            tags.append("Physical Asset Exposure")
        else:
            tags.append("Surface Change Detected")

    return tags[:4]


def _build_operational_impacts(
    payload: dict[str, Any], dominant_signal: dict[str, Any] | None, quality_band: str
) -> list[str]:
    lens = resolve_lens(payload.get("lens"))
    threat_level = str(payload.get("threat_level", "none"))
    radius_km = float(payload.get("query", {}).get("radius_km", 25.0))
    impacts = [
        f"AOI spans roughly {radius_km:.0f} km around the selected coordinates for asset and operations screening.",
        lens.impact_focus,
    ]
    if dominant_signal:
        impacts.append(
            f"Primary driver is {dominant_signal['label'].lower()} via {dominant_signal['source']}."
        )
        hazard = dominant_signal.get("hazard_type")
        if hazard in {"geopolitical", "geopolitical-composite", "drone-missile"}:
            impacts.append("Expect elevated people-safety, route-planning, and continuity risk if escalation persists.")
        elif hazard in {"earthquake", "global-alert"}:
            impacts.append("Physical infrastructure and supplier uptime should be treated as the immediate exposure surface.")
        else:
            impacts.append("Satellite-led surface change indicates on-the-ground conditions are shifting and should be rechecked.")
    if threat_level in {"critical", "high"}:
        impacts.append("This alert level supports paid workflows such as client escalation, dispatching, and protective action briefings.")
    elif threat_level == "medium":
        impacts.append("This is suited to analyst triage queues and scheduled rescan workflows before operational impact hardens.")
    else:
        impacts.append("Current output is better for watchkeeping than escalation, but it preserves an evidence trail for trend detection.")
    impacts.append(f"Current evidence quality is {quality_band}, so downstream customers can judge actionability rather than just score.")
    return impacts[:4]


def _build_next_steps(payload: dict[str, Any], quality_band: str) -> list[str]:
    lens = resolve_lens(payload.get("lens"))
    mode = str(payload.get("mode", "sample"))
    threat_level = str(payload.get("threat_level", "none"))
    next_steps = [
        lens.action_focus,
    ]
    if mode == "sample":
        next_steps.append("Switch to live mode before customer delivery so Sentinel and external feeds reflect the current operating picture.")
    elif not payload.get("query", {}).get("deep_live"):
        next_steps.append("Enable Deep Live imagery when you need a stronger satellite read instead of the fast STAC scout estimate.")

    if threat_level in {"critical", "high"}:
        next_steps.append("Create or scan a watchlist to rank nearby assets and expose the highest-risk hotspot immediately.")
    elif threat_level == "medium":
        next_steps.append("Rescan on a tighter window or higher-sensitivity profile to see whether corroboration is increasing.")
    else:
        next_steps.append("Keep the location on a watchlist and use history to detect upward movement before issuing alerts.")

    if quality_band == "limited":
        next_steps.append("Treat this as an intelligence lead; seek more corroboration before converting it into customer-facing action.")
    return next_steps[:4]


def _build_mission_brief(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload.get("query", {})
    lens = resolve_lens(payload.get("lens"))
    lat = float(query.get("lat", 0.0))
    lon = float(query.get("lon", 0.0))
    coverage = float(payload.get("explainability", {}).get("coverage", 0.0) or 0.0)
    consensus = float(payload.get("explainability", {}).get("consensus", 0.0) or 0.0)
    confidence_score = float(payload.get("confidence_score", 0.0) or 0.0)
    dominant_signal = _dominant_signal(payload)
    quality_band = _quality_band(coverage, consensus, confidence_score)
    source_health = _source_health_summary(payload)
    evidence_health = payload.get("evidence_health") or _build_evidence_health(payload)
    tags = _build_customer_tags(payload, dominant_signal)
    impacts = _build_operational_impacts(payload, dominant_signal, quality_band)
    next_steps = _build_next_steps(payload, quality_band)
    mode_label = "Sample demo" if payload.get("mode") == "sample" else (
        "Live deep imagery" if query.get("deep_live") else "Live fast scout"
    )
    headline = {
        "critical": "Immediate escalation detected",
        "high": "High-consequence hazard pattern detected",
        "medium": "Escalation signals require analyst review",
        "low": "Low-severity monitor state",
        "none": "No actionable hazard trigger detected",
    }.get(str(payload.get("threat_level", "none")), "Location analysis complete")
    signal_summary = (
        f" Dominant signal: {dominant_signal['label']} ({dominant_signal['status']})."
        if dominant_signal
        else ""
    )
    return {
        "headline": headline,
        "summary": (
            f"{mode_label} completed for {lat:.3f}, {lon:.3f} with "
            f"{str(payload.get('threat_level', 'none')).upper()} risk and "
            f"{str(payload.get('confidence', 'low')).upper()} confidence for the {lens.label} lens."
            f"{signal_summary}"
        ),
        "quality_band": quality_band,
        "coverage": round(coverage, 4),
        "consensus": round(consensus, 4),
        "analysis_mode_label": mode_label,
        "lens_label": lens.label,
        "lens_summary": lens.description,
        "dominant_signal": dominant_signal,
        "source_health": source_health,
        "evidence_health": evidence_health,
        "customer_tags": tags,
        "operational_impacts": impacts,
        "next_steps": next_steps,
        "trend": payload.get("trend"),
    }


def _build_lens_insight(payload: dict[str, Any]) -> dict[str, Any]:
    lens = resolve_lens(payload.get("lens"))
    threat_level = str(payload.get("threat_level", "none"))
    dominant_signal = _dominant_signal(payload)
    evidence_health = payload.get("evidence_health", {}) if isinstance(payload.get("evidence_health"), dict) else {}
    trend = payload.get("trend", {}) if isinstance(payload.get("trend"), dict) else {}

    signal_label = dominant_signal.get("label") if isinstance(dominant_signal, dict) else None
    signal_source = dominant_signal.get("source") if isinstance(dominant_signal, dict) else None
    health_label = str(evidence_health.get("overall_label", "unknown"))
    trend_label = str(trend.get("trend_label", "new"))

    lens_matter = {
        "general": "This result is best treated as a balanced operating-picture update for general hazard triage.",
        "logistics": "This result matters if it can degrade route reliability, choke-point flow, or supplier timing.",
        "energy": "This result matters if it can degrade facility continuity, corridor access, or operator posture.",
        "insurance": "This result matters if severity is broadening, persisting, or clustering around exposed assets.",
        "humanitarian": "This result matters if it tightens access, raises responder risk, or increases urgency for support.",
        "security": "This result matters if escalation is changing personnel safety, site posture, or continuity risk.",
    }.get(lens.id, "This result matters for customer-facing operational awareness.")

    next_window = {
        "critical": "Act in the next 1-3 hours and treat the location as escalation-first.",
        "high": "Act in the next 1-6 hours and validate the strongest corroborating signals.",
        "medium": "Use the next 6-12 hours for rescan and corroboration before full escalation.",
        "low": "Keep the location on watch over the next 12-24 hours for movement.",
        "none": "No immediate escalation window is indicated; retain it on background monitoring.",
    }.get(threat_level, "Use the next scan window to validate whether conditions are changing.")

    headline_map = {
        "general": {
            "critical": "Balanced hazard posture has moved into immediate escalation.",
            "high": "Balanced hazard posture is elevated and operationally relevant.",
            "medium": "Balanced hazard posture needs analyst review before escalation.",
            "low": "Balanced posture remains in monitor mode.",
            "none": "Balanced posture shows no actionable trigger.",
        },
        "logistics": {
            "critical": "Route and corridor continuity is under immediate pressure.",
            "high": "Supply-chain exposure is elevated around the selected AOI.",
            "medium": "Corridor disruption signals are building and need review.",
            "low": "Logistics posture is watch-only for now.",
            "none": "No logistics intervention trigger is visible yet.",
        },
        "energy": {
            "critical": "Facility continuity risk is now in escalation territory.",
            "high": "Operational continuity risk is elevated for this AOI.",
            "medium": "Continuity signals are building and need tighter watch.",
            "low": "Energy continuity posture remains in monitor mode.",
            "none": "No immediate continuity trigger is visible yet.",
        },
        "insurance": {
            "critical": "Severity and accumulation posture support immediate escalation.",
            "high": "Exposure severity is elevated and commercially relevant.",
            "medium": "Severity trajectory needs confirmation before reserve escalation.",
            "low": "Exposure remains in low-severity watch mode.",
            "none": "No immediate exposure escalation trigger is visible yet.",
        },
        "humanitarian": {
            "critical": "Access and response urgency now support immediate escalation.",
            "high": "Access constraints and urgency are elevated for the AOI.",
            "medium": "Humanitarian access signals are building and need review.",
            "low": "Response posture remains in monitor mode.",
            "none": "No immediate humanitarian trigger is visible yet.",
        },
        "security": {
            "critical": "Security posture supports immediate protective escalation.",
            "high": "Escalation indicators are elevated for personnel and site posture.",
            "medium": "Security signals are rising and require tighter watchkeeping.",
            "low": "Security posture remains in monitor mode.",
            "none": "No immediate security escalation trigger is visible yet.",
        },
    }
    headline = headline_map.get(lens.id, headline_map["general"]).get(threat_level, "Lens-aware insight unavailable.")

    bullets = [lens_matter]
    if signal_label:
        driver_line = f"Primary driver is {signal_label.lower()}."
        if signal_source:
            driver_line = f"{driver_line} Source: {signal_source}."
        bullets.append(driver_line)
    bullets.append(f"Trend posture is {trend_label.replace('_', ' ')} and evidence health is {health_label}.")

    caveat = {
        "demo": "Current output is still in demo/sample evidence mode.",
        "degraded": "Evidence health is degraded, so urgency should be balanced with corroboration risk.",
        "watch": "Evidence is usable, but freshness or consensus is only partial.",
        "healthy": "Evidence health is strong enough for customer-facing interpretation.",
    }.get(health_label, "Evidence quality should be reviewed alongside the threat signal.")

    caveat_tone = {
        "demo": "watch",
        "degraded": "critical",
        "watch": "watch",
        "healthy": "healthy",
    }.get(health_label, "neutral")

    confidence_note = {
        "degraded": "Treat this as an escalation lead until stronger corroboration arrives.",
        "watch": "Use this for operator awareness, but keep corroboration visible in the customer narrative.",
        "demo": "Do not present this as current operational evidence.",
        "healthy": "This is strong enough to support customer-facing operational framing.",
    }.get(health_label, "Review confidence and evidence health together.")

    action_priority = {
        "critical": "escalate",
        "high": "act",
        "medium": "review",
        "low": "monitor",
        "none": "watch",
    }.get(threat_level, "review")

    actions = [
        str(payload.get("recommended_action", lens.action_focus)).strip(),
        next_window,
    ]

    return {
        "headline": headline,
        "bullets": bullets[:3],
        "caveat": caveat,
        "caveat_tone": caveat_tone,
        "confidence_note": confidence_note,
        "actions": actions[:2],
        "lens_label": lens.label,
        "threat_label": threat_level,
        "action_priority": action_priority,
    }


def _incident_context_for_analysis(analysis_key: str | None) -> dict[str, Any] | None:
    if not analysis_key:
        return None
    incident = find_open_incident_by_analysis_key(str(analysis_key))
    if incident is None:
        return None
    return {
        "id": incident.get("id"),
        "title": incident.get("title") or incident.get("location_label") or "Open incident",
        "status": incident.get("status", "open"),
        "location_label": incident.get("location_label"),
        "latest_history_id": incident.get("latest_history_id"),
        "latest_threat_level": incident.get("latest_threat_level"),
        "latest_trend_label": incident.get("latest_trend_label"),
        "updated_at": incident.get("updated_at"),
    }


def _build_watchlist_summary(watchlist: dict[str, Any], results: list[dict[str, Any]], lens_id: str = "general") -> dict[str, Any]:
    lens = resolve_lens(lens_id)
    ok_results = [item for item in results if item.get("ok") is True]
    ranked = sorted(
        ok_results,
        key=lambda item: (
            THREAT_PRIORITY.get(str(item.get("threat_level", "none")), 0),
            float(item.get("score") or 0.0),
        ),
        reverse=True,
    )
    average_score = round(
        sum(float(item.get("score") or 0.0) for item in ok_results) / len(ok_results),
        4,
    ) if ok_results else 0.0
    threat_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "none": 0, "error": 0}
    for item in results:
        if item.get("ok") is not True:
            threat_counts["error"] += 1
            continue
        level = str(item.get("threat_level", "none"))
        threat_counts[level if level in threat_counts else "none"] += 1

    top_hotspot = None
    if ranked:
        candidate = ranked[0]
        top_hotspot = {
            "member_label": candidate.get("member_label"),
            "threat_level": candidate.get("threat_level"),
            "score": candidate.get("score"),
            "confidence": candidate.get("confidence"),
        }

    watchlist_name = str(watchlist.get("name", "watchlist"))
    if top_hotspot is not None:
        summary = (
            f"{watchlist_name} is led by {top_hotspot['member_label']} with "
            f"{str(top_hotspot['threat_level']).upper()} risk for the {lens.label} lens."
        )
    elif threat_counts["error"] > 0:
        summary = f"{watchlist_name} scan produced only failed lookups."
    else:
        summary = f"{watchlist_name} scan found no elevated hotspots."

    actions = [
        lens.watchlist_focus,
        "Use scan history to judge whether risk is persisting or diffusing across the watchlist.",
    ]
    if threat_counts["error"] > 0:
        actions.append("Re-run failed members or downgrade to sample mode if upstream live data is unstable.")

    healthy_members = 0
    watch_members = 0
    degraded_members = 0
    demo_members = 0
    for item in ok_results:
        label = str(item.get("evidence_health", {}).get("overall_label", "")).strip().lower()
        if label == "healthy":
            healthy_members += 1
        elif label == "watch":
            watch_members += 1
        elif label == "degraded":
            degraded_members += 1
        elif label == "demo":
            demo_members += 1

    if not ok_results:
        health_note = "No successful member analyses were available to assess evidence health."
    elif degraded_members > 0 or watch_members > 0:
        health_note = (
            f"{degraded_members + watch_members} of {len(ok_results)} members ran with degraded or partial evidence health."
        )
    elif demo_members == len(ok_results):
        health_note = "All member analyses are currently based on sample/demo evidence."
    else:
        health_note = "Evidence health is stable across the watchlist."

    return {
        "average_score": average_score,
        "threat_counts": threat_counts,
        "top_hotspot": top_hotspot,
        "summary": summary,
        "actions": actions[:3],
        "lens_label": lens.label,
        "health_note": health_note,
        "health_snapshot": {
            "healthy_members": healthy_members,
            "watch_members": watch_members,
            "degraded_members": degraded_members,
            "demo_members": demo_members,
        },
    }


def _attach_single_analysis_trend(response: dict[str, Any]) -> dict[str, Any]:
    analysis_key = response.get("query", {}).get("analysis_key")
    if not analysis_key:
        return response
    history_rows = read_all_history()
    points = build_single_analysis_trend_points(history_rows, str(analysis_key))
    trend = build_trend_summary(points)
    response["trend"] = trend
    response.setdefault("brief", {})["trend"] = trend
    response["lens_insight"] = _build_lens_insight(response)
    return response


def _attach_watchlist_trends(summary: dict[str, Any], watchlist_id: str, lens: str) -> dict[str, Any]:
    trends = build_watchlist_trend_summary(read_all_history(), watchlist_id, lens=lens)
    summary["trends"] = trends
    return summary


def _incident_location_label(query: dict[str, Any]) -> str:
    try:
        lat = float(query.get("lat", 0.0))
        lon = float(query.get("lon", 0.0))
    except (TypeError, ValueError):
        return "Unknown location"
    return f"{lat:.3f}, {lon:.3f}"


def _incident_fields_from_export(
    export_payload: dict[str, Any],
    history_record: dict[str, Any],
    *,
    title_override: str | None = None,
) -> dict[str, Any]:
    query = export_payload.get("query", {}) if isinstance(export_payload.get("query"), dict) else {}
    brief = export_payload.get("brief", {}) if isinstance(export_payload.get("brief"), dict) else {}
    trend = export_payload.get("trend", {}) if isinstance(export_payload.get("trend"), dict) else {}
    evidence_health = (
        export_payload.get("evidence_health", {})
        if isinstance(export_payload.get("evidence_health"), dict)
        else {}
    )

    return {
        "title": title_override or brief.get("headline") or _incident_location_label(query),
        "location_label": _incident_location_label(query),
        "analysis_key": history_record.get("analysis_key") or query.get("analysis_key"),
        "latest_history_id": history_record.get("id"),
        "query": query,
        "brief_headline": brief.get("headline"),
        "summary": brief.get("summary"),
        "latest_threat_level": export_payload.get("threat_level"),
        "latest_score": export_payload.get("score"),
        "latest_trend_label": trend.get("trend_label"),
        "latest_trend_summary": trend.get("summary"),
        "lens": export_payload.get("lens") or query.get("lens"),
        "lens_label": export_payload.get("lens_label") or brief.get("lens_label"),
        "evidence_health_label": evidence_health.get("overall_label"),
        "latest_updated_at": export_payload.get("generated_at") or history_record.get("created_at"),
    }


def _serialize_incidents() -> list[dict[str, Any]]:
    items = list_incidents()
    ordered = sorted(items, key=lambda item: str(item.get("updated_at", "")), reverse=True)
    return sorted(ordered, key=lambda item: str(item.get("status", "open")) != "open")


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _map_intensity(score: Any, threat_level: Any, *, lens_match: bool = False) -> float:
    score_value = _as_float(score) or 0.0
    floor = {
        "critical": 0.94,
        "high": 0.76,
        "medium": 0.54,
        "low": 0.28,
        "none": 0.12,
    }.get(str(threat_level or "none").lower(), 0.12)
    intensity = max(score_value, floor)
    if lens_match:
        intensity = min(1.0, intensity + 0.06)
    return round(_clamp(intensity, 0.08, 1.0), 4)


def _heat_radius_km(radius_km: Any, source_type: str) -> float:
    base = _clamp(_as_float(radius_km) or 25.0, 8.0, 120.0)
    if source_type == "watchlist":
        return round(_clamp(base * 0.72, 8.0, 38.0), 1)
    if source_type == "incident":
        return round(_clamp(base * 0.88, 10.0, 60.0), 1)
    return round(base, 1)


def _latest_analysis_history(limit: int = 36) -> list[dict[str, Any]]:
    latest_by_key: dict[str, dict[str, Any]] = {}
    for row in read_all_history():
        if row.get("type") != "single_analysis":
            continue
        query = row.get("query", {}) if isinstance(row.get("query"), dict) else {}
        analysis_key = str(row.get("analysis_key") or query.get("analysis_key") or "").strip()
        if not analysis_key:
            continue
        latest_by_key[analysis_key] = row
    ordered = sorted(
        latest_by_key.values(),
        key=lambda row: _parse_iso_datetime(row.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return ordered[:limit]


def _analysis_map_point(row: dict[str, Any], active_lens: str) -> dict[str, Any] | None:
    query = row.get("query", {}) if isinstance(row.get("query"), dict) else {}
    lat = _as_float(query.get("lat"))
    lon = _as_float(query.get("lon"))
    if lat is None or lon is None:
        return None
    export_payload = row.get("export_payload", {}) if isinstance(row.get("export_payload"), dict) else {}
    brief = export_payload.get("brief", {}) if isinstance(export_payload.get("brief"), dict) else {}
    dominant_signal = brief.get("dominant_signal", {}) if isinstance(brief.get("dominant_signal"), dict) else {}
    alert = row.get("alert", {}) if isinstance(row.get("alert"), dict) else {}
    lens = str(row.get("lens") or query.get("lens") or "general")
    threat_level = str(alert.get("threat_level", "none"))
    intensity = _map_intensity(alert.get("score"), threat_level, lens_match=lens == active_lens)
    return {
        "id": str(row.get("id", "")),
        "analysis_key": str(row.get("analysis_key") or query.get("analysis_key") or ""),
        "source_type": "analysis",
        "lat": lat,
        "lon": lon,
        "radius_km": _heat_radius_km(query.get("radius_km"), "analysis"),
        "threat_level": threat_level,
        "score": alert.get("score"),
        "confidence": alert.get("confidence"),
        "lens": lens,
        "label": brief.get("headline") or _incident_location_label(query),
        "summary": brief.get("summary") or "Recent single-location analysis.",
        "signal_label": dominant_signal.get("label") or row.get("brief", {}).get("dominant_signal_label"),
        "quality_band": brief.get("quality_band") or row.get("brief", {}).get("quality_band"),
        "updated_at": row.get("created_at"),
        "intensity": intensity,
    }


def _latest_watchlist_scans() -> list[dict[str, Any]]:
    latest_by_watchlist: dict[str, dict[str, Any]] = {}
    for row in read_all_history():
        if row.get("type") != "watchlist_scan":
            continue
        watchlist_id = str(row.get("watchlist_id", "")).strip()
        if not watchlist_id:
            continue
        latest_by_watchlist[watchlist_id] = row
    return list(latest_by_watchlist.values())


def _watchlist_map_points(active_lens: str) -> list[dict[str, Any]]:
    watchlists_by_id = {str(item.get("id", "")): item for item in list_watchlists()}
    points: list[dict[str, Any]] = []
    for row in _latest_watchlist_scans():
        watchlist_id = str(row.get("watchlist_id", "")).strip()
        watchlist = watchlists_by_id.get(watchlist_id)
        if watchlist is None:
            continue
        members = {
            str(member.get("label", "")).strip(): member
            for member in watchlist.get("members", [])
            if isinstance(member, dict)
        }
        for result in row.get("results", []):
            if not isinstance(result, dict) or result.get("ok") is not True:
                continue
            label = str(result.get("member_label", "")).strip()
            member = members.get(label)
            if member is None:
                continue
            lat = _as_float(member.get("lat"))
            lon = _as_float(member.get("lon"))
            if lat is None or lon is None:
                continue
            lens = str(row.get("lens") or "general")
            threat_level = str(result.get("threat_level", "none"))
            points.append(
                {
                    "id": f"{watchlist_id}:{label}",
                    "watchlist_id": watchlist_id,
                    "watchlist_name": watchlist.get("name"),
                    "member_label": label,
                    "source_type": "watchlist",
                    "lat": lat,
                    "lon": lon,
                    "radius_km": _heat_radius_km(25.0, "watchlist"),
                    "threat_level": threat_level,
                    "score": result.get("score"),
                    "confidence": result.get("confidence"),
                    "lens": lens,
                    "label": label,
                    "summary": row.get("summary", {}).get("summary") or f"Watchlist member from {watchlist.get('name')}.",
                    "signal_label": None,
                    "quality_band": None,
                    "updated_at": row.get("created_at"),
                    "intensity": _map_intensity(result.get("score"), threat_level, lens_match=lens == active_lens),
                }
            )
    return points


def _incident_markers(active_lens: str) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for incident in _serialize_incidents():
        if str(incident.get("status", "open")) != "open":
            continue
        query = incident.get("query", {}) if isinstance(incident.get("query"), dict) else {}
        lat = _as_float(query.get("lat"))
        lon = _as_float(query.get("lon"))
        if lat is None or lon is None:
            continue
        lens = str(incident.get("lens") or query.get("lens") or "general")
        threat_level = str(incident.get("latest_threat_level", "none"))
        markers.append(
            {
                "id": str(incident.get("id", "")),
                "incident_id": str(incident.get("id", "")),
                "source_type": "incident",
                "lat": lat,
                "lon": lon,
                "radius_km": _heat_radius_km(query.get("radius_km"), "incident"),
                "threat_level": threat_level,
                "score": incident.get("latest_score"),
                "lens": lens,
                "label": incident.get("location_label") or incident.get("title") or "Incident",
                "summary": incident.get("brief_headline") or incident.get("summary") or "Open incident.",
                "trend_label": incident.get("latest_trend_label"),
                "health_label": incident.get("evidence_health_label"),
                "updated_at": incident.get("updated_at"),
                "intensity": _map_intensity(incident.get("latest_score"), threat_level, lens_match=lens == active_lens),
            }
        )
    return markers


def _instability_points() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for zone in list_instability_zones():
        lat = _as_float(zone.get("lat"))
        lon = _as_float(zone.get("lon"))
        if lat is None or lon is None:
            continue
        items.append(
            {
                "id": str(zone.get("name", "")),
                "name": zone.get("name"),
                "lat": lat,
                "lon": lon,
                "radius_km": _clamp(_as_float(zone.get("radius_km")) or 200.0, 80.0, 1000.0),
                "score": _clamp(_as_float(zone.get("score")) or 0.0, 0.0, 1.0),
                "reason": str(zone.get("reason", "")).strip(),
                "category": str(zone.get("category", "instability")),
            }
        )
    return items


def _top_hotspots(points: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    ranked = sorted(
        [
            point
            for point in points
            if THREAT_PRIORITY.get(str(point.get("threat_level", "none")), 0) >= 2 or float(point.get("intensity", 0.0)) >= 0.45
        ],
        key=lambda point: (
            THREAT_PRIORITY.get(str(point.get("threat_level", "none")), 0),
            float(point.get("intensity", 0.0)),
            _parse_iso_datetime(point.get("updated_at")) or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )
    return [
        {
            key: point.get(key)
            for key in (
                "id",
                "analysis_key",
                "watchlist_id",
                "watchlist_name",
                "member_label",
                "incident_id",
                "source_type",
                "lat",
                "lon",
                "radius_km",
                "threat_level",
                "score",
                "confidence",
                "lens",
                "label",
                "summary",
                "signal_label",
                "quality_band",
                "updated_at",
                "intensity",
            )
        }
        for point in ranked[:limit]
    ]


def _preset_map_points(active_lens: str, limit: int = 4) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    score_map = {"critical": 0.92, "high": 0.81, "medium": 0.58, "low": 0.31, "none": 0.12}
    ranked = sorted(
        ANALYSIS_PRESETS,
        key=lambda item: (
            str(item.get("lens", "general")) == active_lens,
            bool(item.get("featured")),
            int(item.get("priority", 0)),
        ),
        reverse=True,
    )
    points: list[dict[str, Any]] = []
    for index, preset in enumerate(ranked[:limit]):
        threat_level = str(preset.get("threat_level", "medium"))
        score = score_map.get(threat_level, 0.58)
        lens = str(preset.get("lens", "general"))
        updated_at = (now - timedelta(minutes=index * 7 + 3)).isoformat()
        points.append(
            {
                "id": f"preset:{preset.get('id')}",
                "preset_id": preset.get("id"),
                "source_type": "preset",
                "lat": preset.get("lat"),
                "lon": preset.get("lon"),
                "radius_km": _heat_radius_km(preset.get("radius_km"), "analysis"),
                "threat_level": threat_level,
                "score": score,
                "confidence": "demo",
                "lens": lens,
                "label": preset.get("name"),
                "summary": preset.get("demo_headline") or preset.get("description") or "Featured demo scenario.",
                "signal_label": preset.get("operator_note"),
                "quality_band": "demo",
                "updated_at": updated_at,
                "intensity": _map_intensity(score, threat_level, lens_match=lens == active_lens),
            }
        )
    return points


def _build_map_layers(active_lens: str) -> dict[str, Any]:
    analysis_points = [point for row in _latest_analysis_history() if (point := _analysis_map_point(row, active_lens))]
    watchlist_points = _watchlist_map_points(active_lens)
    incident_points = _incident_markers(active_lens)
    heatmap_points = analysis_points + watchlist_points + incident_points
    if not heatmap_points:
        heatmap_points = _preset_map_points(active_lens)
    hotspot_markers = _top_hotspots(heatmap_points)
    instability_points = _instability_points()
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lens": active_lens,
        "heatmap_points": heatmap_points,
        "hotspot_markers": hotspot_markers,
        "incident_markers": incident_points,
        "watchlist_markers": watchlist_points,
        "instability_points": instability_points,
        "counts": {
            "heatmap_points": len(heatmap_points),
            "hotspot_markers": len(hotspot_markers),
            "incident_markers": len(incident_points),
            "watchlist_markers": len(watchlist_points),
            "instability_points": len(instability_points),
        },
    }


def _risk_band(score: float | None) -> str:
    numeric = score if isinstance(score, (int, float)) else 0.0
    if numeric >= 0.85:
        return "severe"
    if numeric >= 0.65:
        return "elevated"
    if numeric >= 0.4:
        return "watch"
    return "background"


def _bulletin_lens_boost(item: dict[str, Any], lens: str) -> float:
    title = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    if item.get("kind") == "news":
        return 0.12
    if lens == "security":
        return 0.15 if any(token in title for token in ("incident", "escalation", "strike", "corridor")) else 0.0
    if lens == "logistics":
        return 0.15 if any(token in title for token in ("corridor", "route", "watchlist", "shipping")) else 0.0
    if lens == "energy":
        return 0.15 if any(token in title for token in ("facility", "corridor", "continuity", "site")) else 0.0
    if lens == "insurance":
        return 0.15 if any(token in title for token in ("severity", "breadth", "watch", "exposure")) else 0.0
    if lens == "humanitarian":
        return 0.15 if any(token in title for token in ("access", "urgency", "instability", "incident")) else 0.0
    return 0.0


def _history_signal_bulletins(active_lens: str, limit: int = 2) -> list[dict[str, Any]]:
    if limit <= 0:
        return []

    matching: list[dict[str, Any]] = []
    fallback: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for record in read_recent_history(limit=8):
        if not isinstance(record, dict) or str(record.get("type")) != "single_analysis":
            continue
        export_payload = _normalize_export_record(record)
        query = export_payload.get("query", {}) if isinstance(export_payload.get("query"), dict) else {}
        explainability = export_payload.get("explainability", {}) if isinstance(export_payload.get("explainability"), dict) else {}
        signals = explainability.get("signals", []) if isinstance(explainability.get("signals"), list) else []
        record_lens = str(export_payload.get("lens") or query.get("lens") or "general")
        risk_profile = str(query.get("risk_profile", "balanced"))
        created_at = export_payload.get("generated_at") or record.get("created_at")

        for signal in signals:
            if not isinstance(signal, dict):
                continue
            signal_key = str(signal.get("key", "")).strip()
            if signal_key not in {"headline_conflict", "travel_advisory"}:
                continue
            dedupe_key = (str(export_payload.get("history_id") or record.get("id") or ""), signal_key)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            details = str(signal.get("details", "")).strip()
            region_label, separator, remainder = details.partition(":")
            summary = (remainder or details or "No external feed detail available.").strip()
            score = signal.get("score")
            severity = _threat_level_from_score(float(score), risk_profile) if isinstance(score, (int, float)) else "medium"
            title_prefix = "Live news" if signal_key == "headline_conflict" else "Travel advisory"
            title_target = region_label.strip() or str(export_payload.get("lens_label") or "current AOI")
            source_name = "gdelt" if signal_key == "headline_conflict" else "travel-advisory.info"
            item = {
                "id": f"signal:{export_payload.get('history_id') or record.get('id')}:{signal_key}",
                "kind": "news",
                "severity": severity,
                "source": source_name,
                "title": f"{title_prefix}: {title_target}",
                "summary": summary,
                "created_at": created_at,
                "lat": query.get("lat"),
                "lon": query.get("lon"),
                "radius_km": query.get("radius_km"),
                "lens": record_lens,
                "history_id": export_payload.get("history_id") or record.get("id"),
            }
            if record_lens == active_lens:
                matching.append(item)
            else:
                fallback.append(item)

    combined = matching + fallback
    return combined[:limit]


def _build_bulletins(active_lens: str, limit: int = 8) -> list[dict[str, Any]]:
    bulletins: list[dict[str, Any]] = []
    map_layers = _build_map_layers(active_lens)
    hotspots = map_layers.get("hotspot_markers", [])
    incidents = map_layers.get("incident_markers", [])
    instability_items = map_layers.get("instability_points", [])

    for incident in incidents[:4]:
        bulletins.append(
            {
                "id": f"incident:{incident.get('incident_id')}",
                "kind": "operational",
                "severity": str(incident.get("threat_level", "medium")),
                "source": "incident-queue",
                "title": f"Open incident at {incident.get('label')}",
                "summary": incident.get("summary") or "Pinned incident remains active.",
                "created_at": incident.get("updated_at"),
                "lat": incident.get("lat"),
                "lon": incident.get("lon"),
                "radius_km": incident.get("radius_km"),
                "lens": incident.get("lens") or active_lens,
                "incident_id": incident.get("incident_id"),
            }
        )

    bulletins.extend(_history_signal_bulletins(active_lens, limit=2))

    for hotspot in hotspots[:4]:
        bulletins.append(
            {
                "id": f"hotspot:{hotspot.get('id')}",
                "kind": "operational",
                "severity": str(hotspot.get("threat_level", "medium")),
                "source": hotspot.get("source_type", "hotspot"),
                "title": f"Hotspot: {hotspot.get('label')}",
                "summary": hotspot.get("summary") or "Elevated hotspot detected in the current operating picture.",
                "created_at": hotspot.get("updated_at"),
                "lat": hotspot.get("lat"),
                "lon": hotspot.get("lon"),
                "radius_km": hotspot.get("radius_km"),
                "lens": hotspot.get("lens") or active_lens,
                "watchlist_id": hotspot.get("watchlist_id"),
                "analysis_key": hotspot.get("analysis_key"),
            }
        )

    for zone in sorted(instability_items, key=lambda item: float(item.get("score") or 0.0), reverse=True)[:3]:
        bulletins.append(
            {
                "id": f"instability:{zone.get('id')}",
                "kind": "operational",
                "severity": "high" if float(zone.get("score") or 0.0) >= 0.84 else "medium",
                "source": "instability-index",
                "title": f"{zone.get('name')} remains elevated",
                "summary": zone.get("reason") or "Aegis instability model is flagging this corridor.",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "lat": zone.get("lat"),
                "lon": zone.get("lon"),
                "radius_km": zone.get("radius_km"),
                "lens": active_lens,
                "category": zone.get("category"),
            }
        )

    scored = []
    for item in bulletins:
        base = THREAT_PRIORITY.get(str(item.get("severity", "none")), 0) / 4.0
        scored.append((base + _bulletin_lens_boost(item, active_lens), item))
    ordered = [item for _score, item in sorted(scored, key=lambda pair: pair[0], reverse=True)]
    return ordered[:limit]


def _build_instability_index(active_lens: str, limit: int = 6) -> list[dict[str, Any]]:
    weighted: list[dict[str, Any]] = []
    for zone in _instability_points():
        score = float(zone.get("score") or 0.0)
        if active_lens == "security" and zone.get("category") == "strike-risk":
            score = min(1.0, score + 0.08)
        elif active_lens == "logistics" and "corridor" in str(zone.get("name", "")).lower():
            score = min(1.0, score + 0.06)
        elif active_lens == "humanitarian" and zone.get("category") == "instability":
            score = min(1.0, score + 0.05)
        weighted.append(
            {
                **zone,
                "score": round(score, 4),
                "band": _risk_band(score),
            }
        )
    return sorted(weighted, key=lambda item: float(item.get("score") or 0.0), reverse=True)[:limit]


def _build_dashboard_overview(active_lens: str) -> dict[str, Any]:
    map_layers = _build_map_layers(active_lens)
    incidents = map_layers.get("incident_markers", [])
    hotspots = map_layers.get("hotspot_markers", [])
    bulletins = _build_bulletins(active_lens, limit=5)
    instability = _build_instability_index(active_lens, limit=5)
    top_hotspot = hotspots[0] if hotspots else None
    top_instability = instability[0] if instability else None
    latest_history = read_recent_history(limit=1)
    latest_record = latest_history[0] if latest_history else None
    latest_mode = str(latest_record.get("mode", "sample")) if isinstance(latest_record, dict) else "sample"
    degraded_live = latest_mode == "live" and not bool(
        latest_record.get("query", {}).get("deep_live") if isinstance(latest_record.get("query"), dict) else False
    )
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lens": active_lens,
        "counts": {
            "open_incidents": len(incidents),
            "hotspots": len(hotspots),
            "watchlists": len(list_watchlists()),
            "bulletins": len(bulletins),
        },
        "top_hotspot": top_hotspot,
        "top_instability": top_instability,
        "degraded_live": degraded_live,
        "system_note": (
            "Live Fast posture is active in recent scans; satellite evidence can be proxy-weighted."
            if degraded_live
            else "Terminal context is healthy and ready for customer-facing monitoring."
        ),
        "recent_bulletins": bulletins,
        "instability_summary": instability,
    }


def _perform_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    lat = _parse_float(payload, "lat")
    lon = _parse_float(payload, "lon")
    radius_km = _parse_radius_km(payload)
    lat = _clamp(lat, -90.0, 90.0)
    lon = _clamp(lon, -180.0, 180.0)

    mode = str(payload.get("mode", "sample")).lower()
    use_sample = mode != "live"
    response_mode = "sample" if use_sample else "live"
    deep_live = _parse_bool(payload, "deep_live", default=False)
    use_live_fast = (response_mode == "live") and LIVE_FAST_MODE_DEFAULT and (not deep_live)
    risk_profile = str(payload.get("risk_profile", "balanced")).strip().lower()
    if risk_profile not in VALID_RISK_PROFILES:
        risk_profile = "balanced"
    lens = _parse_lens(payload)

    now = datetime.now(timezone.utc).date()
    start_date = str(payload.get("start_date", (now - timedelta(days=30)).isoformat()))
    end_date = str(payload.get("end_date", now.isoformat()))
    bbox = _point_to_bbox(lat, lon, km_radius=radius_km)

    app.logger.info(
        "Analyze request started: mode=%s lat=%.5f lon=%.5f start=%s end=%s",
        response_mode,
        lat,
        lon,
        start_date,
        end_date,
    )

    alert = _run_pipeline_with_timeout(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        use_sample=use_sample,
        use_live_fast=use_live_fast,
        risk_profile=risk_profile,
    )

    response = _normalize_alert_response(
        alert=alert,
        lat=lat,
        lon=lon,
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        mode=response_mode,
        risk_profile=risk_profile,
        lens=lens,
        radius_km=radius_km,
        deep_live=deep_live,
    )
    analysis_key = _analysis_key_from_query(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        mode=response_mode,
        risk_profile=risk_profile,
        lens=lens,
        deep_live=deep_live,
    )
    response["query"]["analysis_key"] = analysis_key
    response["incident_context"] = _incident_context_for_analysis(analysis_key)

    notify_cfg = payload.get("notify") if isinstance(payload.get("notify"), dict) else {}
    notifications = notify_alert(
        response,
        webhook_url=str(notify_cfg.get("webhook_url", "")).strip() or None,
        email_to=str(notify_cfg.get("email_to", "")).strip() or None,
    )
    response["notifications"] = notifications
    response = _attach_single_analysis_trend(response)

    history_entry = append_history(
        {
            "type": "single_analysis",
            "analysis_key": analysis_key,
            "dominant_signal_key": _dominant_signal_key(response),
            "mode": response_mode,
            "lens": lens,
            "query": response["query"],
            "alert": {
                "threat_level": response["threat_level"],
                "score": response["score"],
                "confidence": response["confidence"],
                "recommended_action": response["recommended_action"],
            },
            "brief": _brief_snapshot(response),
            "notifications": notifications,
            "export_payload": {**_analysis_export_payload(response), "history_id": None},
        }
    )
    response["history_id"] = history_entry["id"]
    app.logger.info(
        "Analyze request completed: mode=%s profile=%s threat=%s score=%s",
        response_mode,
        risk_profile,
        response["threat_level"],
        response["score"],
    )
    return response


def _run_pipeline_with_timeout(
    bbox: list[float],
    start_date: str,
    end_date: str,
    use_sample: bool,
    use_live_fast: bool = False,
    risk_profile: str = "balanced",
) -> dict[str, Any]:
    future = _PIPELINE_EXECUTOR.submit(
        run_pipeline,
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        use_sample=use_sample,
        use_live_fast=use_live_fast,
        risk_profile=risk_profile,
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


@app.get("/api/presets")
def get_presets() -> Any:
    items = sorted(
        ANALYSIS_PRESETS,
        key=lambda item: (bool(item.get("featured")), int(item.get("priority", 0))),
        reverse=True,
    )
    featured = next((item for item in items if item.get("featured")), items[0] if items else None)
    return jsonify({"ok": True, "featured_id": featured.get("id") if featured else None, "items": items})


@app.get("/api/lenses")
def get_lenses() -> Any:
    return jsonify({"ok": True, "items": available_lenses()})


@app.get("/api/map/layers")
def get_map_layers() -> Any:
    lens = _parse_lens(request.args.to_dict(flat=True))
    return jsonify(_build_map_layers(lens))


@app.get("/api/feed/bulletins")
def get_bulletins() -> Any:
    lens = _parse_lens(request.args.to_dict(flat=True))
    limit_raw = request.args.get("limit", "8")
    try:
        limit = max(1, min(20, int(limit_raw)))
    except ValueError:
        limit = 8
    return jsonify({"ok": True, "lens": lens, "items": _build_bulletins(lens, limit=limit)})


@app.get("/api/instability")
def get_instability() -> Any:
    lens = _parse_lens(request.args.to_dict(flat=True))
    limit_raw = request.args.get("limit", "6")
    try:
        limit = max(1, min(20, int(limit_raw)))
    except ValueError:
        limit = 6
    items = _build_instability_index(lens, limit=limit)
    return jsonify(
        {
            "ok": True,
            "lens": lens,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "items": items,
            "top_item": items[0] if items else None,
        }
    )


@app.get("/api/dashboard/overview")
def get_dashboard_overview() -> Any:
    lens = _parse_lens(request.args.to_dict(flat=True))
    return jsonify(_build_dashboard_overview(lens))


@app.get("/api/trends")
def get_trends() -> Any:
    payload: dict[str, Any] = request.args.to_dict(flat=True)
    try:
        lat = _clamp(_parse_float(payload, "lat"), -90.0, 90.0)
        lon = _clamp(_parse_float(payload, "lon"), -180.0, 180.0)
        radius_km = _parse_radius_km(payload)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    mode = str(payload.get("mode", "sample")).strip().lower()
    if mode not in {"sample", "live"}:
        mode = "sample"
    risk_profile = str(payload.get("risk_profile", "balanced")).strip().lower()
    if risk_profile not in VALID_RISK_PROFILES:
        risk_profile = "balanced"
    lens = _parse_lens(payload)
    deep_live = _parse_bool(payload, "deep_live", default=False)
    analysis_key = _analysis_key_from_query(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        mode=mode,
        risk_profile=risk_profile,
        lens=lens,
        deep_live=deep_live,
    )
    trend = build_trend_summary(build_single_analysis_trend_points(read_all_history(), analysis_key))
    return jsonify(
        {
            "ok": True,
            "analysis_key": analysis_key,
            "query": {
                "lat": lat,
                "lon": lon,
                "radius_km": radius_km,
                "mode": mode,
                "risk_profile": risk_profile,
                "lens": lens,
                "deep_live": deep_live,
            },
            "trend": trend,
        }
    )


@app.post("/api/analyze")
def analyze_location() -> Any:
    payload = request.get_json(silent=True) or {}

    try:
        response = _perform_analysis(payload)
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
    return jsonify(response)


@app.get("/api/history")
def get_history() -> Any:
    limit_raw = request.args.get("limit", "20")
    try:
        limit = max(1, min(200, int(limit_raw)))
    except ValueError:
        limit = 20
    return jsonify({"ok": True, "items": read_recent_history(limit=limit)})


@app.get("/api/incidents")
def get_incident_queue() -> Any:
    return jsonify({"ok": True, "items": _serialize_incidents()})


@app.post("/api/incidents")
def create_incident_entry() -> Any:
    payload = request.get_json(silent=True) or {}
    history_id = str(payload.get("history_id", "")).strip()
    if not history_id:
        return jsonify({"ok": False, "error": "history_id is required"}), 400

    history_record = read_history_by_id(history_id)
    if history_record is None:
        return jsonify({"ok": False, "error": "history record not found"}), 404
    if history_record.get("type") != "single_analysis":
        return jsonify({"ok": False, "error": "only single analysis records can become incidents"}), 400

    export_payload = _normalize_export_record(history_record)
    analysis_key = str(history_record.get("analysis_key") or export_payload.get("query", {}).get("analysis_key") or "")
    title_override = str(payload.get("title", "")).strip() or None
    fields = _incident_fields_from_export(export_payload, history_record, title_override=title_override)

    existing = find_open_incident_by_analysis_key(analysis_key) if analysis_key else None
    if existing is not None:
        incident = update_incident(existing["id"], fields)
        if incident is None:
            return jsonify({"ok": False, "error": "incident update failed"}), 500
        return jsonify({"ok": True, "incident": incident, "created": False})

    incident = create_incident(fields)
    return jsonify({"ok": True, "incident": incident, "created": True}), 201


@app.post("/api/incidents/<incident_id>/rescan")
def rescan_incident(incident_id: str) -> Any:
    incident = get_incident(incident_id)
    if incident is None:
        return jsonify({"ok": False, "error": "incident not found"}), 404
    if str(incident.get("status", "open")) != "open":
        return jsonify({"ok": False, "error": "incident is closed"}), 400

    query = incident.get("query")
    if not isinstance(query, dict):
        return jsonify({"ok": False, "error": "incident query is missing"}), 400

    try:
        analysis = _perform_analysis(query)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except TimeoutError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 504
    except Exception as exc:  # pragma: no cover
        app.logger.exception("Incident rescan failed")
        return jsonify({"ok": False, "error": str(exc)}), 500

    history_record = read_history_by_id(str(analysis.get("history_id", "")))
    if history_record is None:
        return jsonify({"ok": False, "error": "rescan history record missing"}), 500

    export_payload = _normalize_export_record(history_record)
    incident = update_incident(
        incident_id,
        _incident_fields_from_export(export_payload, history_record, title_override=str(incident.get("title", "")).strip() or None),
    )
    if incident is None:
        return jsonify({"ok": False, "error": "incident update failed"}), 500
    return jsonify({"ok": True, "incident": incident, "analysis": analysis})


@app.post("/api/incidents/<incident_id>/close")
def close_incident_entry(incident_id: str) -> Any:
    incident = close_incident(incident_id)
    if incident is None:
        return jsonify({"ok": False, "error": "incident not found"}), 404
    return jsonify({"ok": True, "incident": incident})


@app.get("/api/watchlists")
def get_watchlists() -> Any:
    return jsonify({"ok": True, "items": list_watchlists()})


@app.delete("/api/watchlists/<watchlist_id>")
def delete_watchlist_entry(watchlist_id: str) -> Any:
    deleted = delete_watchlist(watchlist_id)
    if deleted is None:
        return jsonify({"ok": False, "error": "watchlist not found"}), 404
    return jsonify({"ok": True, "watchlist": deleted})


@app.get("/api/watchlists/<watchlist_id>/trends")
def get_watchlist_trends(watchlist_id: str) -> Any:
    watchlist = get_watchlist(watchlist_id)
    if watchlist is None:
        return jsonify({"ok": False, "error": "watchlist not found"}), 404
    lens = _parse_lens(request.args.to_dict(flat=True))
    trends = build_watchlist_trend_summary(read_all_history(), watchlist_id, lens=lens)
    return jsonify(
        {
            "ok": True,
            "watchlist": {"id": watchlist.get("id"), "name": watchlist.get("name")},
            "lens": lens,
            "trends": trends,
        }
    )


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


@app.put("/api/watchlists/<watchlist_id>/alerts")
def put_watchlist_alerts(watchlist_id: str) -> Any:
    payload = request.get_json(silent=True) or {}
    alerts = _normalize_watchlist_alerts(payload)
    updated = update_watchlist_alerts(
        watchlist_id,
        {
            **alerts,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    if updated is None:
        return jsonify({"ok": False, "error": "watchlist not found"}), 404
    return jsonify({"ok": True, "watchlist": updated})


@app.post("/api/watchlists/<watchlist_id>/scan")
def scan_watchlist(watchlist_id: str) -> Any:
    watchlist = get_watchlist(watchlist_id)
    if watchlist is None:
        return jsonify({"ok": False, "error": "watchlist not found"}), 404

    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "sample")).lower()
    use_sample = mode != "live"
    response_mode = "sample" if use_sample else "live"
    deep_live = _parse_bool(payload, "deep_live", default=False)
    use_live_fast = (response_mode == "live") and LIVE_FAST_MODE_DEFAULT and (not deep_live)
    risk_profile = str(payload.get("risk_profile", "balanced")).strip().lower()
    if risk_profile not in VALID_RISK_PROFILES:
        risk_profile = "balanced"
    lens = _parse_lens(payload)
    try:
        radius_km = _parse_radius_km(payload)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    now = datetime.now(timezone.utc).date()
    start_date = str(payload.get("start_date", (now - timedelta(days=30)).isoformat()))
    end_date = str(payload.get("end_date", now.isoformat()))

    notify_cfg = payload.get("notify") if isinstance(payload.get("notify"), dict) else {}
    saved_alerts = _normalize_watchlist_alerts(watchlist.get("alerts"))
    effective_alerts = {
        **saved_alerts,
        "email_to": str(notify_cfg.get("email_to", saved_alerts.get("email_to", ""))).strip(),
        "sms_to": str(notify_cfg.get("sms_to", saved_alerts.get("sms_to", ""))).strip(),
        "email_enabled": bool(notify_cfg.get("email_enabled", saved_alerts.get("email_enabled", False))),
        "sms_enabled": bool(notify_cfg.get("sms_enabled", saved_alerts.get("sms_enabled", False))),
        "threshold": str(notify_cfg.get("threshold", saved_alerts.get("threshold", "high"))).strip().lower() or "high",
    }
    if effective_alerts["threshold"] not in {"medium", "high", "critical"}:
        effective_alerts["threshold"] = "high"
    results: list[dict[str, Any]] = []
    for member in watchlist.get("members", []):
        lat = float(member["lat"])
        lon = float(member["lon"])
        bbox = _point_to_bbox(lat, lon, km_radius=radius_km)
        try:
            alert = _run_pipeline_with_timeout(
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                use_sample=use_sample,
                use_live_fast=use_live_fast,
                risk_profile=risk_profile,
            )
            response = _normalize_alert_response(
                alert=alert,
                lat=lat,
                lon=lon,
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                mode=response_mode,
                risk_profile=risk_profile,
                lens=lens,
                radius_km=radius_km,
                deep_live=deep_live,
            )
            response["member_label"] = str(member.get("label", "member"))
            response["query"]["analysis_key"] = _analysis_key_from_query(
                lat=lat,
                lon=lon,
                radius_km=radius_km,
                mode=response_mode,
                risk_profile=risk_profile,
                lens=lens,
                deep_live=deep_live,
            )
            response["notifications"] = []
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
                        "lens": lens,
                        "radius_km": radius_km,
                        "deep_live": deep_live,
                    },
                    "error": str(exc),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
            )

    summary = _build_watchlist_summary(watchlist, results, lens_id=lens)
    summary = _attach_watchlist_trends(summary, watchlist_id, lens)

    for result in results:
        if result.get("ok") is not True:
            continue
        alert_package = _build_watchlist_alert_package(
            watchlist=watchlist,
            summary=summary,
            results=results,
            mode=response_mode,
            lens=lens,
            triggered_result=result,
        )
        result["notifications"] = notify_alert(
            result,
            webhook_url=str(notify_cfg.get("webhook_url", "")).strip() or None,
            email_to=effective_alerts["email_to"] if effective_alerts["email_enabled"] else None,
            html_body=alert_package["html_body"] if effective_alerts["email_enabled"] else None,
            sms_to=effective_alerts["sms_to"] if effective_alerts["sms_enabled"] else None,
            sms_message=alert_package["sms_message"] if effective_alerts["sms_enabled"] else None,
            minimum_level=effective_alerts["threshold"],
        )

    history_entry = append_history(
        {
            "type": "watchlist_scan",
            "watchlist_id": watchlist_id,
            "mode": response_mode,
            "lens": lens,
            "result_count": len(results),
            "summary": summary,
            "results": [
                {
                    "member_label": r.get("member_label"),
                    "analysis_key": r.get("query", {}).get("analysis_key"),
                    "threat_level": r.get("threat_level", "error"),
                    "score": r.get("score"),
                    "confidence": r.get("confidence"),
                    "dominant_signal_key": _dominant_signal_key(r),
                    "ok": bool(r.get("ok", False)),
                }
                for r in results
            ],
            "export_payload": _watchlist_export_payload(
                watchlist=watchlist,
                summary=summary,
                results=results,
                mode=response_mode,
                lens=lens,
            ),
        }
    )

    return jsonify(
        {
            "ok": True,
            "watchlist": {"id": watchlist.get("id"), "name": watchlist.get("name")},
            "results": results,
            "summary": summary,
            "history_id": history_entry["id"],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
