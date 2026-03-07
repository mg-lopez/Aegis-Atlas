"""Minimal Watch -> Navigate -> Analyze -> Deliver agent skeleton with CLI."""

from __future__ import annotations

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import sqrt
from pathlib import Path
from typing import Any

import requests


from analyze import analyze_sample_tiffs, analyze_scene_pair
from risk_intel import (
    conflict_headline_score,
    drone_strike_likelihood_score,
    regional_conflict_score,
    reverse_geocode_country,
    travel_advisory_score,
)
from stac_fetcher import SceneSummary, find_best_sentinel_scenes, scene_to_dict

LOGGER = logging.getLogger(__name__)
DEBUG_DIR = Path(__file__).resolve().parent / "demo" / "debug"

DEMO_TRIGGER_BBOX = (-119.5, 33.5, -117.0, 35.2)
DEMO_SEISMIC_TRIGGER_BBOX = (138.5, 34.5, 142.5, 38.5)

@dataclass(frozen=True)
class RiskProfileConfig:
    name: str
    sentinel_weight: float
    gdacs_weight: float
    usgs_weight: float
    geo_conflict_weight: float
    geo_context_component_weight: float
    drone_component_weight: float
    travel_component_weight: float
    headline_component_weight: float
    critical_threshold: float
    high_threshold: float
    medium_threshold: float


RISK_PROFILES: dict[str, RiskProfileConfig] = {
    "conservative": RiskProfileConfig(
        name="conservative",
        sentinel_weight=0.60,
        gdacs_weight=0.15,
        usgs_weight=0.10,
        geo_conflict_weight=0.15,
        geo_context_component_weight=0.45,
        drone_component_weight=0.35,
        travel_component_weight=0.15,
        headline_component_weight=0.05,
        critical_threshold=0.92,
        high_threshold=0.58,
        medium_threshold=0.30,
    ),
    "balanced": RiskProfileConfig(
        name="balanced",
        sentinel_weight=0.35,
        gdacs_weight=0.15,
        usgs_weight=0.10,
        geo_conflict_weight=0.40,
        geo_context_component_weight=0.30,
        drone_component_weight=0.40,
        travel_component_weight=0.10,
        headline_component_weight=0.20,
        critical_threshold=0.82,
        high_threshold=0.45,
        medium_threshold=0.30,
    ),
    "sensitive": RiskProfileConfig(
        name="sensitive",
        sentinel_weight=0.25,
        gdacs_weight=0.15,
        usgs_weight=0.20,
        geo_conflict_weight=0.40,
        geo_context_component_weight=0.25,
        drone_component_weight=0.45,
        travel_component_weight=0.10,
        headline_component_weight=0.20,
        critical_threshold=0.74,
        high_threshold=0.40,
        medium_threshold=0.22,
    ),
}

STATUS_BASE_SCORE = {
    "ok": None,
    "no_event": 0.03,
    "insufficient_data": 0.14,
    "unavailable": 0.18,
}

STATUS_RELIABILITY = {
    "ok": 1.0,
    "no_event": 0.35,
    "insufficient_data": 0.25,
    "unavailable": 0.20,
}


@dataclass(frozen=True)
class HazardEvent:
    region: list[float]
    hazard_type: str
    source: str
    magnitude: float | None = None


@dataclass(frozen=True)
class HazardSignal:
    key: str
    source: str
    hazard_type: str
    score: float | None
    weight: float
    status: str
    details: str


def _resolve_risk_profile(profile: str | None) -> RiskProfileConfig:
    normalized = (profile or "balanced").strip().lower()
    return RISK_PROFILES.get(normalized, RISK_PROFILES["balanced"])


def _ensure_debug_dir() -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    return DEBUG_DIR


def _write_debug_json(filename: str, payload: dict) -> None:
    path = _ensure_debug_dir() / filename
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _bboxes_overlap(a: list[float], b: tuple[float, float, float, float]) -> bool:
    a_min_lon, a_min_lat, a_max_lon, a_max_lat = a
    b_min_lon, b_min_lat, b_max_lon, b_max_lat = b
    return not (
        a_max_lon < b_min_lon
        or a_min_lon > b_max_lon
        or a_max_lat < b_min_lat
        or a_min_lat > b_max_lat
    )


def poll_gdacs(bbox: list[float]) -> list[HazardEvent]:
    if _bboxes_overlap(bbox, DEMO_TRIGGER_BBOX):
        return [HazardEvent(region=bbox, hazard_type="wildfire", source="gdacs-demo")]
    return []


def poll_usgs_earthquakes(
    bbox: list[float],
    start_date: str,
    end_date: str,
    min_magnitude: float = 3.5,
) -> list[HazardEvent]:
    params = {
        "format": "geojson",
        "starttime": start_date,
        "endtime": end_date,
        "minlatitude": bbox[1],
        "maxlatitude": bbox[3],
        "minlongitude": bbox[0],
        "maxlongitude": bbox[2],
        "minmagnitude": min_magnitude,
        "orderby": "time",
        "limit": 30,
    }
    try:
        response = requests.get(
            "https://earthquake.usgs.gov/fdsnws/event/1/query",
            params=params,
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
        events: list[HazardEvent] = []
        for feature in payload.get("features", []):
            props = feature.get("properties", {})
            magnitude = props.get("mag")
            if magnitude is None:
                continue
            events.append(
                HazardEvent(
                    region=bbox,
                    hazard_type="earthquake",
                    source="usgs",
                    magnitude=float(magnitude),
                )
            )
        return events
    except Exception as exc:  # pragma: no cover - network instability
        LOGGER.warning("USGS adapter unavailable: %s", exc)
        if _bboxes_overlap(bbox, DEMO_SEISMIC_TRIGGER_BBOX):
            return [HazardEvent(region=bbox, hazard_type="earthquake", source="usgs-demo", magnitude=5.8)]
        return []


def navigate_to_scenes(bbox: list[float], start_date: str, end_date: str) -> list[SceneSummary]:
    scenes = find_best_sentinel_scenes(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud=80.0,
        limit=10,
    )
    _write_debug_json("stac_listing.json", {"scenes": [scene_to_dict(s) for s in scenes]})
    return scenes


def watch_for_trigger(
    bbox: list[float],
    start_date: str,
    end_date: str,
) -> tuple[str | None, list[SceneSummary], str | None]:
    gdacs_events = poll_gdacs(bbox)
    if gdacs_events:
        return "gdacs", [], None

    try:
        fallback_scenes = find_best_sentinel_scenes(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            max_cloud=80.0,
            limit=10,
        )
        _write_debug_json("stac_listing.json", {"scenes": [scene_to_dict(s) for s in fallback_scenes]})
    except Exception:
        return None, [], "No GDACS trigger found and STAC fallback check failed."

    if fallback_scenes:
        return "stac", fallback_scenes, None

    return None, [], "No GDACS trigger and no Sentinel-2 scenes found for region/date range."



def _select_scenes_with_baseline(
    scenes: list[SceneSummary], bbox: list[float], start_date: str
) -> tuple[list[SceneSummary], bool, list[SceneSummary]]:
    selected_recent = sorted(scenes, key=lambda s: s.datetime, reverse=True)[:2]
    if len(selected_recent) >= 2:
        return selected_recent, False, []

    baseline_scenes: list[SceneSummary] = []
    fallback_used = False
    baseline_end = (datetime.fromisoformat(start_date) - timedelta(days=1)).date()
    baseline_start = baseline_end - timedelta(days=364)

    try:
        older = find_best_sentinel_scenes(
            bbox=bbox,
            start_date=baseline_start.isoformat(),
            end_date=baseline_end.isoformat(),
            max_cloud=80.0,
            limit=5,
        )
    except Exception:
        older = []

    if older:
        fallback_used = True
        baseline_scenes = sorted(older, key=lambda s: s.datetime, reverse=True)[:1]
        combined = selected_recent + baseline_scenes
        return combined, fallback_used, baseline_scenes

    return selected_recent, fallback_used, baseline_scenes


def analyze_recent_change(
    scenes: list[SceneSummary], bbox: list[float], start_date: str, end_date: str
) -> tuple[float | None, list[SceneSummary]]:
    selected, used_fallback, baseline_scenes = _select_scenes_with_baseline(
        scenes, bbox=bbox, start_date=start_date
    )
    _write_debug_json(
        "scene_selection.json",
        {
            "bbox": bbox,
            "date_window": {"start_date": start_date, "end_date": end_date},
            "recent_scenes_selected": [scene_to_dict(s) for s in scenes],
            "baseline_fallback_used": used_fallback,
            "baseline_scenes": [scene_to_dict(s) for s in baseline_scenes],
            "analysis_pair": [scene_to_dict(s) for s in selected],
        },
    )

    if len(selected) < 2:
        return None, selected

    recent, baseline = sorted(selected, key=lambda s: s.datetime, reverse=True)[:2]
    metrics = analyze_scene_pair(baseline, recent)
    return float(metrics["final_score"]), [recent, baseline]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _signal_from_satellite(score: float | None, no_baseline: bool, risk_profile: RiskProfileConfig) -> HazardSignal:
    if score is None and no_baseline:
        return HazardSignal(
            key="sentinel_change",
            source="sentinel-2",
            hazard_type="surface-change",
            score=None,
            weight=risk_profile.sentinel_weight,
            status="insufficient_data",
            details="Insufficient baseline/recent pair for satellite change score.",
        )
    if score is None:
        return HazardSignal(
            key="sentinel_change",
            source="sentinel-2",
            hazard_type="surface-change",
            score=None,
            weight=risk_profile.sentinel_weight,
            status="unavailable",
            details="Sentinel-2 score unavailable for current time window.",
        )
    return HazardSignal(
        key="sentinel_change",
        source="sentinel-2",
        hazard_type="surface-change",
        score=_clamp01(float(score)),
        weight=risk_profile.sentinel_weight,
        status="ok",
        details="Spectral and structural scene-delta analysis.",
    )


def _signal_from_stac_metadata(scenes: list[SceneSummary], risk_profile: RiskProfileConfig) -> HazardSignal:
    if not scenes:
        return HazardSignal(
            key="sentinel_change",
            source="sentinel-2",
            hazard_type="surface-change",
            score=None,
            weight=risk_profile.sentinel_weight,
            status="unavailable",
            details="No STAC scenes available for metadata-based estimate.",
        )

    clouds = [float(scene.cloud_cover) for scene in scenes if scene.cloud_cover is not None]
    best_cloud = min(clouds) if clouds else 80.0
    # Fast live mode proxy is intentionally conservative to avoid over-inflating base risk.
    estimated_score = _clamp01((30.0 - best_cloud) / 30.0 * 0.35)
    return HazardSignal(
        key="sentinel_change",
        source="sentinel-2-stac-meta",
        hazard_type="surface-change",
        score=estimated_score,
        weight=risk_profile.sentinel_weight,
        status="ok",
        details=f"Fast-mode estimate from STAC metadata (best cloud cover {best_cloud:.1f}%).",
    )


def _signal_from_geo_context(
    bbox: list[float], risk_profile: RiskProfileConfig | None = None
) -> HazardSignal:
    active_profile = risk_profile or _resolve_risk_profile("balanced")
    center_lat = (bbox[1] + bbox[3]) / 2.0
    center_lon = (bbox[0] + bbox[2]) / 2.0
    score, reason = regional_conflict_score(center_lat, center_lon)
    if score is None:
        return HazardSignal(
            key="geo_conflict_context",
            source="regional-risk-model",
            hazard_type="geopolitical",
            score=STATUS_BASE_SCORE["no_event"],
            weight=active_profile.geo_context_component_weight,
            status="no_event",
            details=reason,
        )
    return HazardSignal(
        key="geo_conflict_context",
        source="regional-risk-model",
        hazard_type="geopolitical",
        score=score,
        weight=active_profile.geo_context_component_weight,
        status="ok",
        details=reason,
    )


def _signal_from_drone_strike_likelihood(bbox: list[float], risk_profile: RiskProfileConfig) -> HazardSignal:
    center_lat = (bbox[1] + bbox[3]) / 2.0
    center_lon = (bbox[0] + bbox[2]) / 2.0
    score, reason = drone_strike_likelihood_score(center_lat, center_lon)
    return HazardSignal(
        key="drone_missile_likelihood",
        source="regional-strike-model",
        hazard_type="drone-missile",
        score=score,
        weight=risk_profile.drone_component_weight,
        status="ok" if score >= 0.10 else "no_event",
        details=reason,
    )


def _signal_from_travel_advisory_and_headlines(
    bbox: list[float], risk_profile: RiskProfileConfig
) -> list[HazardSignal]:
    center_lat = (bbox[1] + bbox[3]) / 2.0
    center_lon = (bbox[0] + bbox[2]) / 2.0
    country = reverse_geocode_country(center_lat, center_lon)
    if country is None:
        return [
            HazardSignal(
                key="travel_advisory",
                source="travel-advisory.info",
                hazard_type="government-advisory",
                score=STATUS_BASE_SCORE["unavailable"],
                weight=risk_profile.travel_component_weight,
                status="unavailable",
                details="Country resolution unavailable for advisory lookup.",
            ),
            HazardSignal(
                key="headline_conflict",
                source="gdelt",
                hazard_type="headline-cluster",
                score=STATUS_BASE_SCORE["unavailable"],
                weight=risk_profile.headline_component_weight,
                status="unavailable",
                details="Country resolution unavailable for headline lookup.",
            ),
        ]

    country_code, country_name = country

    with ThreadPoolExecutor(max_workers=2) as pool:
        travel_future = pool.submit(travel_advisory_score, country_code)
        news_future = pool.submit(conflict_headline_score, country_name)
        try:
            travel_score, travel_reason = travel_future.result(timeout=6)
        except FuturesTimeoutError:
            travel_score, travel_reason = None, "Travel advisory lookup timed out."
        try:
            news_score, news_reason = news_future.result(timeout=6)
        except FuturesTimeoutError:
            news_score, news_reason = None, "Headline cluster lookup timed out."

    def _status_from_reason(score: float | None, reason: str) -> str:
        if score is None:
            return "unavailable"
        normalized_reason = reason.lower()
        if "unavailable" in normalized_reason or "timed out" in normalized_reason:
            return "unavailable"
        if "stale cache" in normalized_reason or "rate-limited" in normalized_reason:
            return "insufficient_data"
        return "ok"

    travel_status = _status_from_reason(travel_score, travel_reason)
    news_status = _status_from_reason(news_score, news_reason)
    travel_signal = HazardSignal(
        key="travel_advisory",
        source="travel-advisory.info",
        hazard_type="government-advisory",
        score=travel_score if travel_score is not None else STATUS_BASE_SCORE["unavailable"],
        weight=risk_profile.travel_component_weight,
        status=travel_status,
        details=f"{country_code}: {travel_reason}",
    )
    news_signal = HazardSignal(
        key="headline_conflict",
        source="gdelt",
        hazard_type="headline-cluster",
        score=news_score if news_score is not None else STATUS_BASE_SCORE["unavailable"],
        weight=risk_profile.headline_component_weight,
        status=news_status,
        details=f"{country_name}: {news_reason}",
    )
    return [travel_signal, news_signal]


def _combine_component_signals(signals: list[HazardSignal]) -> tuple[float, str]:
    total_weight = 0.0
    weighted_score = 0.0
    for signal in signals:
        reliability = STATUS_RELIABILITY.get(signal.status, 0.5)
        effective_weight = signal.weight * reliability
        total_weight += effective_weight
        weighted_score += _clamp01(float(signal.score or 0.0)) * effective_weight

    fused = weighted_score / total_weight if total_weight > 0 else 0.0
    component_details = ", ".join(
        f"{signal.key}={_clamp01(float(signal.score or 0.0)):.2f} ({signal.status})" for signal in signals
    )
    return _clamp01(fused), component_details


def _signal_from_geo_conflict_fusion(bbox: list[float], risk_profile: RiskProfileConfig) -> HazardSignal:
    geo_context = _signal_from_geo_context(bbox, risk_profile=risk_profile)
    drone_component = _signal_from_drone_strike_likelihood(bbox, risk_profile=risk_profile)
    geo_component = HazardSignal(
        key="regional_conflict_context",
        source=geo_context.source,
        hazard_type=geo_context.hazard_type,
        score=geo_context.score,
        weight=risk_profile.geo_context_component_weight,
        status=geo_context.status,
        details=geo_context.details,
    )
    travel_component, headline_component = _signal_from_travel_advisory_and_headlines(
        bbox, risk_profile=risk_profile
    )
    components = [geo_component, drone_component, travel_component, headline_component]
    fused_score, component_details = _combine_component_signals(components)
    ok_count = sum(1 for signal in components if signal.status == "ok")
    unavailable_count = sum(1 for signal in components if signal.status == "unavailable")
    if ok_count == 0 and unavailable_count == len(components):
        status = "unavailable"
    elif ok_count == 0:
        status = "insufficient_data"
    else:
        status = "ok"

    return HazardSignal(
        key="geo_conflict",
        source="regional-risk-model+travel-advisory+gdelt",
        hazard_type="geopolitical-composite",
        score=fused_score,
        weight=risk_profile.geo_conflict_weight,
        status=status,
        details=f"Composite from regional context, travel advisory, and headline intensity: {component_details}.",
    )


def _signal_from_gdacs(bbox: list[float], risk_profile: RiskProfileConfig) -> HazardSignal:
    events = poll_gdacs(bbox)
    if not events:
        return HazardSignal(
            key="gdacs",
            source="gdacs",
            hazard_type="global-alert",
            score=STATUS_BASE_SCORE["no_event"],
            weight=risk_profile.gdacs_weight,
            status="no_event",
            details="No active GDACS event intersecting selected AOI.",
        )
    return HazardSignal(
        key="gdacs",
        source=events[0].source,
        hazard_type=events[0].hazard_type,
        score=0.78,
        weight=risk_profile.gdacs_weight,
        status="ok",
        details=f"GDACS event overlap detected ({events[0].hazard_type}).",
    )


def _signal_from_usgs(
    bbox: list[float], start_date: str, end_date: str, risk_profile: RiskProfileConfig
) -> HazardSignal:
    events = poll_usgs_earthquakes(bbox, start_date=start_date, end_date=end_date)
    if not events:
        return HazardSignal(
            key="usgs_seismic",
            source="usgs",
            hazard_type="earthquake",
            score=STATUS_BASE_SCORE["no_event"],
            weight=risk_profile.usgs_weight,
            status="no_event",
            details="No USGS earthquakes above magnitude threshold in time window.",
        )
    strongest_mag = max((event.magnitude or 0.0) for event in events)
    normalized = _clamp01((strongest_mag - 3.0) / 4.0)
    return HazardSignal(
        key="usgs_seismic",
        source=events[0].source,
        hazard_type="earthquake",
        score=normalized,
        weight=risk_profile.usgs_weight,
        status="ok",
        details=f"{len(events)} seismic events found; strongest magnitude {strongest_mag:.1f}.",
    )


def _collect_external_signals(
    bbox: list[float], start_date: str, end_date: str, risk_profile: RiskProfileConfig
) -> list[HazardSignal]:
    signals = [
        _signal_from_gdacs(bbox, risk_profile=risk_profile),
        _signal_from_usgs(bbox, start_date=start_date, end_date=end_date, risk_profile=risk_profile),
        _signal_from_geo_conflict_fusion(bbox, risk_profile=risk_profile),
    ]
    return signals


def _threat_level_from_score(score: float | None, risk_profile: RiskProfileConfig) -> str:
    if score is None:
        return "none"
    if score >= risk_profile.critical_threshold:
        return "critical"
    if score >= risk_profile.high_threshold:
        return "high"
    if score >= risk_profile.medium_threshold:
        return "medium"
    return "low"


def _confidence_label(confidence_score: float) -> str:
    if confidence_score >= 0.75:
        return "high"
    if confidence_score >= 0.45:
        return "medium"
    return "low"


def fuse_signals(signals: list[HazardSignal], risk_profile: RiskProfileConfig | None = None) -> dict[str, Any]:
    active_profile = risk_profile or _resolve_risk_profile("balanced")
    normalized_signals: list[HazardSignal] = []
    for signal in signals:
        if signal.score is None:
            imputed = STATUS_BASE_SCORE.get(signal.status, STATUS_BASE_SCORE["unavailable"])
            normalized_signals.append(
                HazardSignal(
                    key=signal.key,
                    source=signal.source,
                    hazard_type=signal.hazard_type,
                    score=imputed,
                    weight=signal.weight,
                    status=signal.status,
                    details=signal.details,
                )
            )
            continue
        normalized_signals.append(signal)

    raw_active = [signal for signal in signals if signal.score is not None]
    total_weight = sum(signal.weight for signal in normalized_signals)
    weighted_sum = 0.0
    effective_weight_total = 0.0
    for signal in normalized_signals:
        reliability = STATUS_RELIABILITY.get(signal.status, 0.5)
        effective_weight = signal.weight * reliability
        weighted_sum += _clamp01(float(signal.score or 0.0)) * effective_weight
        effective_weight_total += effective_weight

    fused_score = (weighted_sum / effective_weight_total) if effective_weight_total > 0 else 0.0

    if len(normalized_signals) >= 2:
        mean = sum((signal.score or 0.0) for signal in normalized_signals) / len(normalized_signals)
        variance = (
            sum((((signal.score or 0.0) - mean) ** 2) for signal in normalized_signals) / len(normalized_signals)
        )
        spread = min(1.0, sqrt(variance) / 0.5)
        consensus = 1.0 - spread
    elif len(normalized_signals) == 1:
        consensus = 0.75
    else:
        consensus = 0.0

    coverage = (effective_weight_total / total_weight) if total_weight > 0 else 0.0
    confidence_score = _clamp01(0.15 + 0.55 * coverage + 0.30 * consensus)

    ranked = sorted(
        normalized_signals,
        key=lambda signal: (signal.score or 0.0) * signal.weight * STATUS_RELIABILITY.get(signal.status, 0.5),
        reverse=True,
    )
    rationale = [
        (
            f"{signal.key}: score {signal.score:.2f} with weight {signal.weight:.2f} "
            f"and reliability {STATUS_RELIABILITY.get(signal.status, 0.5):.2f} ({signal.details})"
        )
        for signal in ranked
    ]

    explainability = {
        "active_signal_count": len(raw_active),
        "scored_signal_count": len(normalized_signals),
        "coverage": round(coverage, 4),
        "consensus": round(consensus, 4),
        "aggregation": "reliability_weighted_mean",
        "signals": [
            {
                "key": signal.key,
                "source": signal.source,
                "hazard_type": signal.hazard_type,
                "status": signal.status,
                "score": None if signal.score is None else round(signal.score, 4),
                "weight": signal.weight,
                "reliability": STATUS_RELIABILITY.get(signal.status, 0.5),
                "effective_weight": round(signal.weight * STATUS_RELIABILITY.get(signal.status, 0.5), 4),
                "contribution": None if signal.score is None else round(signal.score * signal.weight, 4),
                "details": signal.details,
            }
            for signal in normalized_signals
        ],
    }

    return {
        "fused_score": round(_clamp01(fused_score), 4),
        "confidence_score": round(confidence_score, 4),
        "confidence": _confidence_label(confidence_score),
        "threat_level": _threat_level_from_score(fused_score if normalized_signals else None, active_profile),
        "rationale": rationale,
        "explainability": explainability,
    }


def _recommended_action(threat_level: str, no_signal_reason: str | None = None) -> str:
    if threat_level == "critical":
        return "Execute evacuation now and follow official emergency instructions immediately."
    if threat_level == "high":
        return "Immediate evacuation advised; verify with authorities and proceed to nearest safe zone."
    if threat_level == "medium":
        return "Prepare to evacuate; monitor updates and assemble emergency kit."
    if threat_level == "low":
        return "No immediate action required; continue monitoring."
    return no_signal_reason or "Monitor and corroborate; insufficient multi-source evidence."


def deliver_alert(
    region: list[float],
    source_scenes: list[SceneSummary],
    signals: list[HazardSignal],
    risk_profile: RiskProfileConfig | None = None,
    no_signal_reason: str | None = None,
) -> dict[str, Any]:
    active_profile = risk_profile or _resolve_risk_profile("balanced")
    fusion = fuse_signals(signals, risk_profile=active_profile)
    raw_active_count = int(fusion.get("explainability", {}).get("active_signal_count", 0))
    threat_level = fusion["threat_level"]
    score = fusion["fused_score"]
    if raw_active_count == 0 and no_signal_reason:
        threat_level = "none"
        score = 0.0

    return {
        "region": region,
        "threat_level": threat_level,
        "score": score if threat_level != "none" else 0.0,
        "score_label": _threat_level_from_score(score, active_profile) if threat_level != "none" else "none",
        "risk_profile": active_profile.name,
        "confidence": fusion["confidence"],
        "confidence_score": fusion["confidence_score"],
        "recommended_action": _recommended_action(threat_level, no_signal_reason=no_signal_reason),
        "sources": [scene.id for scene in source_scenes],
        "source_details": [scene_to_dict(scene) for scene in source_scenes],
        "rationale": fusion["rationale"],
        "explainability": fusion["explainability"],
    }


def run_pipeline(
    bbox: list[float],
    start_date: str,
    end_date: str,
    use_sample: bool = False,
    use_live_fast: bool = False,
    risk_profile: str = "balanced",
) -> dict:
    active_profile = _resolve_risk_profile(risk_profile)
    if use_sample:
        demo_dir = Path(__file__).resolve().parent / "demo"
        baseline_path = demo_dir / "sample_baseline.tif"
        recent_path = demo_dir / "sample_recent.tif"

        if not baseline_path.exists() or not recent_path.exists():
            from demo.generate_sample_tiffs import generate_sample_tiffs

            baseline_path, recent_path = generate_sample_tiffs(demo_dir)

        metrics = analyze_sample_tiffs(baseline_path, recent_path)
        sample_scenes = [
            SceneSummary(id=baseline_path.name, datetime=start_date, cloud_cover=0.0, assets={}),
            SceneSummary(id=recent_path.name, datetime=end_date, cloud_cover=0.0, assets={}),
        ]
        # Keep sample mode deterministic around satellite demo artifacts.
        signals = [_signal_from_satellite(float(metrics["final_score"]), no_baseline=False, risk_profile=active_profile)]
        return deliver_alert(region=bbox, source_scenes=sample_scenes, signals=signals, risk_profile=active_profile)

    trigger_source, fallback_scenes, no_trigger_reason = watch_for_trigger(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
    )
    source_scenes: list[SceneSummary] = []
    score: float | None = None
    no_baseline = False
    satellite_signal: HazardSignal | None = None

    if trigger_source is not None:
        if use_live_fast and trigger_source == "stac":
            source_scenes = fallback_scenes[:3]
            satellite_signal = _signal_from_stac_metadata(source_scenes, risk_profile=active_profile)
        else:
            scenes = navigate_to_scenes(bbox, start_date=start_date, end_date=end_date)
            score, compared = analyze_recent_change(scenes, bbox=bbox, start_date=start_date, end_date=end_date)
            no_baseline = score is None
            if trigger_source == "stac":
                compared_ids = {scene.id for scene in compared}
                source_scenes = compared + [scene for scene in fallback_scenes if scene.id not in compared_ids]
            else:
                source_scenes = compared

    signals = [satellite_signal or _signal_from_satellite(score, no_baseline=no_baseline, risk_profile=active_profile)]
    signals.extend(
        _collect_external_signals(
            bbox,
            start_date=start_date,
            end_date=end_date,
            risk_profile=active_profile,
        )
    )
    return deliver_alert(
        region=bbox,
        source_scenes=source_scenes,
        signals=signals,
        risk_profile=active_profile,
        no_signal_reason=no_trigger_reason,
    )


def run_demo(bbox: list[float], start_date: str, end_date: str, use_sample: bool = False) -> dict:
    return run_pipeline(bbox=bbox, start_date=start_date, end_date=end_date, use_sample=use_sample)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aegis Atlas agent skeleton")
    parser.add_argument("--log-level", default="INFO")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--bbox", required=True)
    run_parser.add_argument("--start_date", required=True)
    run_parser.add_argument("--end_date", required=True)
    run_parser.add_argument("--risk_profile", choices=sorted(RISK_PROFILES.keys()), default="balanced")
    return parser


def _parse_bbox_string(bbox_str: str) -> list[float]:
    parts = [p.strip() for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError("--bbox must have exactly 4 comma-separated values")
    return [float(p) for p in parts]


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.command == "run":
        bbox = _parse_bbox_string(args.bbox)
        alert = run_pipeline(
            bbox=bbox,
            start_date=args.start_date,
            end_date=args.end_date,
            risk_profile=args.risk_profile,
        )
        print(json.dumps(alert, indent=2))


if __name__ == "__main__":
    main()
