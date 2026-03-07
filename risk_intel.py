"""Lightweight geopolitical/travel/news risk intelligence adapters."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import requests


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
]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2.0) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


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


def reverse_geocode_country(lat: float, lon: float, timeout_sec: float = 4.0) -> tuple[str, str] | None:
    url = "https://api.bigdatacloud.net/data/reverse-geocode-client"
    params = {
        "latitude": f"{lat:.6f}",
        "longitude": f"{lon:.6f}",
        "localityLanguage": "en",
    }
    try:
        response = requests.get(url, params=params, timeout=timeout_sec)
        response.raise_for_status()
        payload = response.json()
        code = str(payload.get("countryCode", "")).upper()
        name = str(payload.get("countryName", "")).strip()
        if len(code) == 2 and name:
            return code, name
    except Exception:
        return None
    return None


def travel_advisory_score(country_code: str, timeout_sec: float = 4.0) -> tuple[float | None, str]:
    try:
        response = requests.get(
            "https://www.travel-advisory.info/api",
            params={"countrycode": country_code},
            timeout=timeout_sec,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", {}).get(country_code.upper(), {})
        advisory = data.get("advisory", {})
        numeric = advisory.get("score")
        if numeric is None:
            return None, "Travel advisory score unavailable."
        # API score is usually 1..5; normalize to 0..1.
        score = max(0.0, min(1.0, (float(numeric) - 1.0) / 4.0))
        source = advisory.get("source") or "travel-advisory.info"
        return round(score, 4), f"Travel advisory source: {source}, level score {numeric}."
    except Exception:
        return None, "Travel advisory feed unavailable."


def conflict_headline_score(country_name: str, timeout_sec: float = 5.0) -> tuple[float | None, str]:
    # Query conflict-oriented coverage in recent window.
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y%m%d%H%M%S")
    query = f"\"{country_name}\" AND (missile OR strike OR attack OR conflict OR war)"
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": 20,
        "sort": "DateDesc",
        "startdatetime": since,
    }
    try:
        response = requests.get("https://api.gdeltproject.org/api/v2/doc/doc", params=params, timeout=timeout_sec)
        response.raise_for_status()
        payload = response.json()
        articles = payload.get("articles", []) or []
        count = len(articles)
        if count == 0:
            return None, "No recent conflict-heavy headline cluster found."
        # Saturating transform: 1-2 low, 5 medium, 10+ high.
        score = min(1.0, count / 10.0)
        return round(score, 4), f"{count} recent conflict-related headlines in 7-day window."
    except Exception:
        return None, "Headline risk feed unavailable."
