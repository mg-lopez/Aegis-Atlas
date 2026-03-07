"""Trend helpers for analysis history and watchlist monitoring."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

THREAT_PRIORITY = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0, "error": -1}


def build_analysis_key(
    *,
    lat: float,
    lon: float,
    radius_km: float,
    mode: str,
    risk_profile: str,
    lens: str = "general",
    deep_live: bool = False,
) -> str:
    mode_flag = "deep" if (mode == "live" and deep_live) else ("fast" if mode == "live" else "sample")
    return (
        f"{mode.lower()}:{risk_profile.lower()}:{lens.lower()}:{mode_flag}:"
        f"{lat:.4f}:{lon:.4f}:{radius_km:.1f}"
    )


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.min.replace(tzinfo=timezone.utc)


def _round_score(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _trend_label(points: list[dict[str, Any]]) -> str:
    if not points:
        return "insufficient"
    if len(points) == 1:
        return "new"

    scores = [float(point["score"]) for point in points if isinstance(point.get("score"), (int, float))]
    if len(scores) < 2:
        return "insufficient"

    latest = scores[-1]
    previous = scores[-2]
    delta = latest - previous
    score_range = max(scores) - min(scores)
    sign_changes = 0
    for idx in range(2, len(scores)):
        left = scores[idx - 1] - scores[idx - 2]
        right = scores[idx] - scores[idx - 1]
        if (left > 0 > right) or (left < 0 < right):
            sign_changes += 1

    if len(scores) >= 3 and score_range >= 0.22 and sign_changes >= 1 and abs(delta) < 0.05:
        return "volatile"
    if delta >= 0.08:
        return "rising"
    if delta <= -0.08:
        return "falling"
    if score_range >= 0.18 and sign_changes >= 1:
        return "volatile"
    return "stable"


def _trend_summary_text(label: str, latest_score: float | None, delta_score: float | None, point_count: int) -> str:
    if point_count == 0:
        return "No prior scans available."
    if point_count == 1:
        return "First recorded scan for this location."
    latest_text = "n/a" if latest_score is None else f"{latest_score:.2f}"
    delta_text = "n/a" if delta_score is None else f"{delta_score:+.2f}"
    if label == "rising":
        return f"Risk is rising versus the prior scan ({delta_text}, latest {latest_text})."
    if label == "falling":
        return f"Risk is easing versus the prior scan ({delta_text}, latest {latest_text})."
    if label == "volatile":
        return f"Recent scans are unstable; risk is oscillating around {latest_text}."
    if label == "stable":
        return f"Risk is broadly stable across recent scans ({delta_text}, latest {latest_text})."
    return "Trend is not established yet."


def build_trend_summary(points: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(points, key=lambda point: _parse_timestamp(point.get("created_at")))
    if not ordered:
        return {
            "point_count": 0,
            "trend_label": "insufficient",
            "delta_score": None,
            "latest_score": None,
            "previous_score": None,
            "latest_threat_level": "none",
            "previous_threat_level": None,
            "dominant_signal_changed": False,
            "sparkline": [],
            "series": [],
            "summary": "No prior scans available.",
        }

    latest = ordered[-1]
    previous = ordered[-2] if len(ordered) >= 2 else None
    latest_score = _round_score(latest.get("score"))
    previous_score = _round_score(previous.get("score")) if previous else None
    delta_score = None if latest_score is None or previous_score is None else round(latest_score - previous_score, 4)
    label = _trend_label(ordered)
    sparkline = [
        float(point["score"])
        for point in ordered[-8:]
        if isinstance(point.get("score"), (int, float))
    ]

    return {
        "point_count": len(ordered),
        "trend_label": label,
        "delta_score": delta_score,
        "latest_score": latest_score,
        "previous_score": previous_score,
        "latest_threat_level": str(latest.get("threat_level", "none")),
        "previous_threat_level": None if previous is None else str(previous.get("threat_level", "none")),
        "dominant_signal_changed": (
            previous is not None
            and bool(latest.get("dominant_signal_key"))
            and latest.get("dominant_signal_key") != previous.get("dominant_signal_key")
        ),
        "latest_dominant_signal_key": latest.get("dominant_signal_key"),
        "sparkline": [round(value, 4) for value in sparkline],
        "series": [
            {
                "created_at": point.get("created_at"),
                "score": _round_score(point.get("score")),
                "threat_level": str(point.get("threat_level", "none")),
                "dominant_signal_key": point.get("dominant_signal_key"),
                "member_label": point.get("member_label"),
            }
            for point in ordered[-8:]
        ],
        "summary": _trend_summary_text(label, latest_score, delta_score, len(ordered)),
    }


def build_single_analysis_trend_points(history_rows: list[dict[str, Any]], analysis_key: str) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for row in history_rows:
        if row.get("type") != "single_analysis":
            continue
        if row.get("analysis_key") != analysis_key:
            continue
        alert = row.get("alert", {})
        points.append(
            {
                "created_at": row.get("created_at"),
                "score": alert.get("score"),
                "threat_level": alert.get("threat_level"),
                "confidence": alert.get("confidence"),
                "dominant_signal_key": row.get("dominant_signal_key"),
                "analysis_key": row.get("analysis_key"),
            }
        )
    return points


def build_watchlist_trend_summary(
    history_rows: list[dict[str, Any]],
    watchlist_id: str,
    lens: str | None = None,
) -> dict[str, Any]:
    member_points: dict[str, list[dict[str, Any]]] = {}
    for row in history_rows:
        if row.get("type") != "watchlist_scan":
            continue
        if row.get("watchlist_id") != watchlist_id:
            continue
        if lens is not None and str(row.get("lens", "general")) != str(lens):
            continue
        created_at = row.get("created_at")
        for result in row.get("results", []):
            member_label = str(result.get("member_label", "member"))
            member_points.setdefault(member_label, []).append(
                {
                    "created_at": created_at,
                    "score": result.get("score"),
                    "threat_level": result.get("threat_level", "none"),
                    "confidence": result.get("confidence"),
                    "dominant_signal_key": result.get("dominant_signal_key"),
                    "member_label": member_label,
                    "analysis_key": result.get("analysis_key"),
                }
            )

    member_summaries: list[dict[str, Any]] = []
    for member_label, points in member_points.items():
        summary = build_trend_summary(points)
        summary["member_label"] = member_label
        member_summaries.append(summary)

    member_summaries.sort(
        key=lambda item: (
            THREAT_PRIORITY.get(str(item.get("latest_threat_level", "none")), 0),
            float(item.get("latest_score") or 0.0),
        ),
        reverse=True,
    )

    biggest_riser = None
    risers = [item for item in member_summaries if isinstance(item.get("delta_score"), (int, float))]
    if risers:
        candidate = max(risers, key=lambda item: float(item.get("delta_score") or 0.0))
        if float(candidate.get("delta_score") or 0.0) > 0:
            biggest_riser = {
                "member_label": candidate["member_label"],
                "delta_score": candidate.get("delta_score"),
                "latest_score": candidate.get("latest_score"),
                "latest_threat_level": candidate.get("latest_threat_level"),
            }

    most_persistent_hotspot = None
    if member_summaries:
        candidate = max(
            member_summaries,
            key=lambda item: (
                sum(float(point.get("score") or 0.0) for point in item.get("series", [])) / max(1, len(item.get("series", []))),
                float(item.get("latest_score") or 0.0),
            ),
        )
        most_persistent_hotspot = {
            "member_label": candidate["member_label"],
            "latest_score": candidate.get("latest_score"),
            "latest_threat_level": candidate.get("latest_threat_level"),
            "trend_label": candidate.get("trend_label"),
        }

    newly_elevated = None
    for item in member_summaries:
        latest_priority = THREAT_PRIORITY.get(str(item.get("latest_threat_level", "none")), 0)
        previous_priority = THREAT_PRIORITY.get(str(item.get("previous_threat_level", "none")), 0)
        if latest_priority >= THREAT_PRIORITY["medium"] and previous_priority < THREAT_PRIORITY["medium"]:
            newly_elevated = {
                "member_label": item["member_label"],
                "latest_score": item.get("latest_score"),
                "latest_threat_level": item.get("latest_threat_level"),
            }
            break

    if biggest_riser is not None:
        summary = f"Biggest riser is {biggest_riser['member_label']} ({biggest_riser['delta_score']:+.2f})."
    elif most_persistent_hotspot is not None:
        summary = f"Most persistent hotspot is {most_persistent_hotspot['member_label']}."
    else:
        summary = "Trend history is still forming for this watchlist."

    return {
        "member_count": len(member_summaries),
        "members": member_summaries,
        "biggest_riser": biggest_riser,
        "most_persistent_hotspot": most_persistent_hotspot,
        "newly_elevated": newly_elevated,
        "summary": summary,
    }
