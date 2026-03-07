"""Lightweight geopolitical/travel/news risk intelligence adapters."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass(frozen=True)
class GeoRiskZone:
    name: str
    lat: float
    lon: float
    radius_km: float
    score: float
    reason: str


_GEO_RISK_ZONES: list[GeoRiskZone] = [
    GeoRiskZone("Ukraine conflict zone", 48.5, 31.0, 700.0, 0.90, "Active interstate conflict risk."),
    GeoRiskZone("Israel/Gaza region", 31.5, 34.8, 350.0, 0.92, "Sustained strike/escalation risk."),
    GeoRiskZone("Lebanon border region", 33.3, 35.4, 180.0, 0.82, "Cross-border escalation risk."),
    GeoRiskZone("Yemen", 15.6, 47.6, 650.0, 0.85, "Armed conflict and strike risk."),
    GeoRiskZone("Syria", 35.0, 38.5, 500.0, 0.82, "Ongoing conflict activity."),
    GeoRiskZone("Sudan", 14.5, 30.2, 850.0, 0.88, "Severe internal conflict conditions."),
    GeoRiskZone("Red Sea corridor", 18.0, 40.0, 520.0, 0.76, "Shipping/missile disruption corridor."),
    GeoRiskZone("Iran strategic belt", 33.5, 52.0, 950.0, 0.84, "Elevated regional strike escalation risk."),
    GeoRiskZone("Persian Gulf corridor", 26.0, 52.0, 700.0, 0.74, "Drone/missile and maritime disruption risk corridor."),
    GeoRiskZone("Iraq-Syria corridor", 34.0, 42.0, 600.0, 0.72, "Militia and cross-border strike corridor."),
    GeoRiskZone("Caucasus transit corridor", 41.5, 46.5, 450.0, 0.60, "Potential spillover route for regional escalation."),
]

_DRONE_STRIKE_ZONES: list[GeoRiskZone] = [
    GeoRiskZone("Tehran strategic area", 35.7, 51.4, 180.0, 0.92, "High-value strategic area with elevated UAV/missile risk."),
    GeoRiskZone("Isfahan strategic area", 32.6, 51.7, 180.0, 0.88, "Strategic military/industrial area with elevated strike risk."),
    GeoRiskZone("Natanz corridor", 33.7, 51.7, 140.0, 0.90, "Documented strategic target corridor."),
    GeoRiskZone("Israel/Gaza strike zone", 31.5, 34.8, 280.0, 0.94, "Persistent rocket/drone/missile strike environment."),
    GeoRiskZone("Southern Lebanon corridor", 33.2, 35.4, 220.0, 0.86, "Cross-border UAV/rocket exchange risk."),
    GeoRiskZone("Red Sea maritime lane", 16.8, 42.5, 500.0, 0.78, "Long-range UAV and missile threat corridor."),
    GeoRiskZone("Black Sea north coast", 46.0, 32.5, 500.0, 0.74, "Long-range strike activity corridor."),
]


def list_instability_zones() -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    for zone in _GEO_RISK_ZONES:
        zones.append(
            {
                "name": zone.name,
                "lat": zone.lat,
                "lon": zone.lon,
                "radius_km": zone.radius_km,
                "score": zone.score,
                "reason": zone.reason,
                "category": "instability",
            }
        )
    for zone in _DRONE_STRIKE_ZONES:
        zones.append(
            {
                "name": zone.name,
                "lat": zone.lat,
                "lon": zone.lon,
                "radius_km": zone.radius_km,
                "score": zone.score,
                "reason": zone.reason,
                "category": "strike-risk",
            }
        )
    return zones


@dataclass
class _CacheEntry:
    payload: Any
    fetched_at: datetime


_SESSION = requests.Session()
_SESSION.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
        )
    ),
)
_CACHE: dict[str, _CacheEntry] = {}
_CACHE_TTL_SEC = 15 * 60
_CACHE_STALE_TTL_SEC = 6 * 60 * 60


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2.0) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _cache_age_minutes(entry: _CacheEntry) -> int:
    return int((datetime.now(timezone.utc) - entry.fetched_at).total_seconds() / 60)


def _cache_get(key: str, ttl_sec: int = _CACHE_TTL_SEC) -> Any | None:
    entry = _CACHE.get(key)
    if entry is None:
        return None
    age_sec = (datetime.now(timezone.utc) - entry.fetched_at).total_seconds()
    if age_sec <= ttl_sec:
        return entry.payload
    return None


def _cache_get_stale(key: str, stale_ttl_sec: int = _CACHE_STALE_TTL_SEC) -> _CacheEntry | None:
    entry = _CACHE.get(key)
    if entry is None:
        return None
    age_sec = (datetime.now(timezone.utc) - entry.fetched_at).total_seconds()
    if age_sec <= stale_ttl_sec:
        return entry
    return None


def _cache_set(key: str, payload: Any) -> None:
    _CACHE[key] = _CacheEntry(payload=payload, fetched_at=datetime.now(timezone.utc))


def _get_json(url: str, params: dict[str, Any], timeout_sec: float) -> dict[str, Any]:
    response = _SESSION.get(url, params=params, timeout=timeout_sec)
    response.raise_for_status()
    return response.json()


def regional_conflict_score(lat: float, lon: float) -> tuple[float | None, str]:
    best_score = 0.0
    best_reason = "Outside defined high-conflict corridors."
    for zone in _GEO_RISK_ZONES:
        distance = _haversine_km(lat, lon, zone.lat, zone.lon)
        if distance > zone.radius_km:
            continue
        attenuation = max(0.0, 1.0 - (distance / zone.radius_km))
        score = zone.score * attenuation
        if score > best_score:
            best_score = score
            best_reason = f"{zone.reason} Proximity to {zone.name} ({distance:.0f} km)."
    if best_score <= 0.0:
        return None, best_reason
    return round(min(1.0, best_score), 4), best_reason


def drone_strike_likelihood_score(lat: float, lon: float) -> tuple[float, str]:
    best_score = 0.02
    best_reason = "No elevated drone/missile strike corridor near selected point."
    for zone in _DRONE_STRIKE_ZONES:
        distance = _haversine_km(lat, lon, zone.lat, zone.lon)
        if distance > zone.radius_km:
            continue
        attenuation = max(0.0, 1.0 - (distance / zone.radius_km))
        score = zone.score * attenuation
        if score > best_score:
            best_score = score
            best_reason = f"{zone.reason} Proximity to {zone.name} ({distance:.0f} km)."
    return round(min(1.0, best_score), 4), best_reason


def reverse_geocode_country(lat: float, lon: float, timeout_sec: float = 4.0) -> tuple[str, str] | None:
    url = "https://api.bigdatacloud.net/data/reverse-geocode-client"
    params = {
        "latitude": f"{lat:.6f}",
        "longitude": f"{lon:.6f}",
        "localityLanguage": "en",
    }
    cache_key = f"reverse_geocode:{params['latitude']}:{params['longitude']}"
    cached = _cache_get(cache_key)
    if cached is not None:
        payload = cached
    else:
        try:
            payload = _get_json(url, params=params, timeout_sec=timeout_sec)
            _cache_set(cache_key, payload)
        except Exception:
            stale = _cache_get_stale(cache_key)
            if stale is None:
                return None
            payload = stale.payload
    try:
        code = str(payload.get("countryCode", "")).upper()
        name = str(payload.get("countryName", "")).strip()
        if len(code) == 2 and name:
            return code, name
    except Exception:
        return None
    return None


def travel_advisory_score(country_code: str, timeout_sec: float = 4.0) -> tuple[float | None, str]:
    normalized_code = country_code.upper().strip()
    cache_key = f"travel_advisory:{normalized_code}"
    cached = _cache_get(cache_key)
    if cached is not None:
        payload = cached
        cache_note = "fresh cache"
    else:
        try:
            payload = _get_json(
                "https://travel-advisory.info/api",
                params={"countrycode": normalized_code},
                timeout_sec=timeout_sec,
            )
            _cache_set(cache_key, payload)
            cache_note = "live"
        except Exception:
            stale = _cache_get_stale(cache_key)
            if stale is None:
                return 0.12, "Travel advisory feed unavailable; using conservative baseline."
            payload = stale.payload
            cache_note = f"stale cache ({_cache_age_minutes(stale)} min old)"

    try:
        data = payload.get("data", {}).get(normalized_code, {})
        advisory = data.get("advisory", {})
        numeric = advisory.get("score")
        if numeric is None:
            return 0.12, "Travel advisory score unavailable; using conservative baseline."
        # API score is usually 1..5; normalize to 0..1.
        score = max(0.0, min(1.0, (float(numeric) - 1.0) / 4.0))
        source = advisory.get("source") or "travel-advisory.info"
        return round(score, 4), f"Travel advisory source: {source}, level score {numeric} ({cache_note})."
    except Exception:
        return 0.12, "Travel advisory feed unavailable; using conservative baseline."


def conflict_headline_score(country_name: str, timeout_sec: float = 5.0) -> tuple[float | None, str]:
    # Query conflict-oriented coverage in recent window.
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y%m%d%H%M%S")
    query = f"\"{country_name}\" AND (missile OR strike OR attack OR conflict OR war)"
    params: dict[str, Any] = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": 10,
        "sort": "DateDesc",
        "startdatetime": since,
    }
    cache_key = f"headline_conflict:{country_name.lower().strip()}"
    cached = _cache_get(cache_key)
    if cached is not None:
        payload = cached
        cache_note = "fresh cache"
    else:
        try:
            payload = _get_json("https://api.gdeltproject.org/api/v2/doc/doc", params=params, timeout_sec=timeout_sec)
            _cache_set(cache_key, payload)
            cache_note = "live"
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 429:
                return 0.05, "Headline risk feed rate-limited; using conservative low score."
            stale = _cache_get_stale(cache_key)
            if stale is None:
                return 0.05, "Headline risk feed unavailable; using conservative low score."
            payload = stale.payload
            cache_note = f"stale cache ({_cache_age_minutes(stale)} min old)"
        except Exception:
            stale = _cache_get_stale(cache_key)
            if stale is None:
                return 0.05, "Headline risk feed unavailable; using conservative low score."
            payload = stale.payload
            cache_note = f"stale cache ({_cache_age_minutes(stale)} min old)"

    try:
        articles = payload.get("articles", []) or []
        count = len(articles)
        if count == 0:
            return 0.05, f"No recent conflict-heavy headline cluster found ({cache_note})."
        # Saturating transform: 1-2 low, 5 medium, 10+ high.
        score = min(1.0, count / 10.0)
        return round(score, 4), f"{count} recent conflict-related headlines in 7-day window ({cache_note})."
    except Exception:
        return 0.05, "Headline risk feed unavailable; using conservative low score."
