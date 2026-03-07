"""Deterministic demo scenarios for threat-level walkthroughs."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians
from pathlib import Path
from typing import Any

from agent_skeleton import HazardSignal, deliver_alert
from stac_fetcher import SceneSummary


@dataclass(frozen=True)
class DemoScenario:
    name: str
    lat: float
    lon: float
    expected_threat_level: str
    description: str
    sentinel_score: float | None
    gdacs_score: float | None
    usgs_score: float | None


SCENARIOS: dict[str, DemoScenario] = {
    "low": DemoScenario(
        name="low",
        lat=51.5072,
        lon=-0.1276,
        expected_threat_level="low",
        description="London baseline monitoring with weak change signal and no external alerts.",
        sentinel_score=0.18,
        gdacs_score=None,
        usgs_score=None,
    ),
    "medium": DemoScenario(
        name="medium",
        lat=34.0522,
        lon=-118.2437,
        expected_threat_level="medium",
        description="Los Angeles scenario with moderate surface change and mild seismic support.",
        sentinel_score=0.42,
        gdacs_score=None,
        usgs_score=0.52,
    ),
    "high": DemoScenario(
        name="high",
        lat=34.3521,
        lon=-118.5820,
        expected_threat_level="high",
        description="Southern California escalation with strong satellite and multi-feed corroboration.",
        sentinel_score=0.84,
        gdacs_score=0.78,
        usgs_score=0.66,
    ),
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _point_to_bbox(lat: float, lon: float, km_radius: float = 25.0) -> list[float]:
    lat_delta = km_radius / 111.0
    cos_lat = max(0.1, cos(radians(lat)))
    lon_delta = km_radius / (111.0 * cos_lat)
    return [
        _clamp(lon - lon_delta, -180.0, 180.0),
        _clamp(lat - lat_delta, -90.0, 90.0),
        _clamp(lon + lon_delta, -180.0, 180.0),
        _clamp(lat + lat_delta, -90.0, 90.0),
    ]


def _signal(
    key: str,
    source: str,
    hazard_type: str,
    score: float | None,
    weight: float,
    no_event_detail: str,
    ok_detail: str,
) -> HazardSignal:
    if score is None:
        return HazardSignal(
            key=key,
            source=source,
            hazard_type=hazard_type,
            score=None,
            weight=weight,
            status="no_event",
            details=no_event_detail,
        )
    return HazardSignal(
        key=key,
        source=source,
        hazard_type=hazard_type,
        score=score,
        weight=weight,
        status="ok",
        details=ok_detail,
    )


def build_scenario_alert(scenario: DemoScenario) -> dict[str, Any]:
    bbox = _point_to_bbox(scenario.lat, scenario.lon)
    signals = [
        _signal(
            key="sentinel_change",
            source="sentinel-2",
            hazard_type="surface-change",
            score=scenario.sentinel_score,
            weight=0.55,
            no_event_detail="Satellite signal unavailable for scenario.",
            ok_detail="Scenario-defined Sentinel-2 delta score.",
        ),
        _signal(
            key="gdacs",
            source="gdacs",
            hazard_type="global-alert",
            score=scenario.gdacs_score,
            weight=0.25,
            no_event_detail="No active GDACS event in scenario.",
            ok_detail="Scenario-defined GDACS overlap score.",
        ),
        _signal(
            key="usgs_seismic",
            source="usgs",
            hazard_type="earthquake",
            score=scenario.usgs_score,
            weight=0.20,
            no_event_detail="No relevant seismic activity in scenario.",
            ok_detail="Scenario-defined USGS severity score.",
        ),
    ]

    source_scenes = [
        SceneSummary(
            id=f"scenario-{scenario.name}-baseline",
            datetime="2024-08-01T00:00:00Z",
            cloud_cover=0.0,
            assets={},
        ),
        SceneSummary(
            id=f"scenario-{scenario.name}-recent",
            datetime="2024-08-31T00:00:00Z",
            cloud_cover=0.0,
            assets={},
        ),
    ]

    alert = deliver_alert(region=bbox, source_scenes=source_scenes, signals=signals)
    alert["scenario"] = {
        "name": scenario.name,
        "lat": scenario.lat,
        "lon": scenario.lon,
        "description": scenario.description,
        "expected_threat_level": scenario.expected_threat_level,
    }
    return alert


def snapshot_paths(project_root: Path) -> tuple[Path, Path]:
    snapshots_dir = project_root / "demo" / "snapshots"
    debug_report = project_root / "demo" / "debug" / "scenario_fusion_report.json"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    debug_report.parent.mkdir(parents=True, exist_ok=True)
    return snapshots_dir, debug_report
