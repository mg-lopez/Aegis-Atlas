"""Minimal Watch -> Navigate -> Analyze -> Deliver agent skeleton with CLI.

This module intentionally keeps each pipeline phase in a dedicated function so the
workflow can be unit tested and extended with real integrations later.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from dataclasses import dataclass

import numpy as np

from analyze import change_score
from stac_fetcher import SceneSummary, find_best_sentinel_scenes

LOGGER = logging.getLogger(__name__)

# Demo polygon roughly around Los Angeles county area.
DEMO_TRIGGER_BBOX = (-119.5, 33.5, -117.0, 35.2)


@dataclass(frozen=True)
class HazardEvent:
    """Represents a hazard trigger emitted by the watch phase."""

    region: list[float]
    hazard_type: str
    source: str


def _bboxes_overlap(a: list[float], b: tuple[float, float, float, float]) -> bool:
    """Return ``True`` when two ``[min_lon, min_lat, max_lon, max_lat]`` bboxes overlap."""

    a_min_lon, a_min_lat, a_max_lon, a_max_lat = a
    b_min_lon, b_min_lat, b_max_lon, b_max_lat = b
    return not (
        a_max_lon < b_min_lon
        or a_min_lon > b_max_lon
        or a_max_lat < b_min_lat
        or a_min_lat > b_max_lat
    )


def poll_gdacs(bbox: list[float]) -> list[HazardEvent]:
    """Watch step placeholder for polling GDACS-like hazard feeds.

    For this demo, we emit a hardcoded wildfire trigger only when the input bbox
    overlaps ``DEMO_TRIGGER_BBOX``.
    """

    if _bboxes_overlap(bbox, DEMO_TRIGGER_BBOX):
        event = HazardEvent(region=bbox, hazard_type="wildfire", source="gdacs-demo")
        LOGGER.info("Watch: trigger found from demo GDACS feed.")
        return [event]

    LOGGER.info("Watch: no active trigger for bbox.")
    return []


def navigate_to_scenes(bbox: list[float], start_date: str, end_date: str) -> list[SceneSummary]:
    """Navigate step: fetch candidate Sentinel-2 scenes from STAC."""

    LOGGER.info("Navigate: querying STAC for candidate scenes.")
    scenes = find_best_sentinel_scenes(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud=20.0,
        limit=10,
    )
    LOGGER.info("Navigate: found %d scenes.", len(scenes))
    return scenes


def watch_for_trigger(
    bbox: list[float],
    start_date: str,
    end_date: str,
) -> tuple[str | None, list[SceneSummary], str | None]:
    """Watch step with GDACS-first trigger selection and STAC fallback.

    Returns a tuple ``(trigger_source, fallback_scenes, no_trigger_reason)`` where
    ``trigger_source`` is one of ``"gdacs"``, ``"stac"``, or ``None`` when no
    trigger is detected.
    """

    gdacs_events = poll_gdacs(bbox)
    if gdacs_events:
        LOGGER.info("Watch: using GDACS trigger; continuing to Navigate/Analyze.")
        return "gdacs", [], None

    LOGGER.info(
        "Watch: no GDACS trigger; falling back to STAC availability check (max_cloud=80)."
    )
    try:
        fallback_scenes = find_best_sentinel_scenes(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            max_cloud=80.0,
            limit=10,
        )
    except ModuleNotFoundError:
        LOGGER.warning("Watch: STAC fallback unavailable; missing STAC dependencies.")
        return None, [], "No GDACS trigger found and STAC fallback is unavailable."
    except Exception as exc:
        LOGGER.warning("Watch: STAC fallback check failed: %s", exc)
        return None, [], "No GDACS trigger found and STAC fallback check failed."

    if fallback_scenes:
        LOGGER.info(
            "Watch: STAC soft trigger found %d scenes; continuing to Analyze.",
            len(fallback_scenes),
        )
        return "stac", fallback_scenes, None

    LOGGER.info("Watch: no GDACS event and no STAC scenes found.")
    return None, [], "No GDACS trigger and no Sentinel-2 scenes found for region/date range."


def _load_demo_rgb(scene: SceneSummary, shape: tuple[int, int, int] = (64, 64, 3)) -> np.ndarray:
    """Load scene RGB for analysis in a deterministic demo-friendly way.

    In a production implementation this would read scene assets and raster data.
    For the skeleton we generate deterministic pseudo-imagery keyed by scene id,
    allowing repeatable tests without network/raster dependencies.
    """

    digest = hashlib.sha256(scene.id.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], byteorder="big", signed=False)
    rng = np.random.default_rng(seed)
    return rng.random(shape, dtype=np.float32)


def analyze_recent_change(scenes: list[SceneSummary]) -> tuple[float, list[SceneSummary]]:
    """Analyze step: load the two most recent scenes and compute ``change_score``."""

    if len(scenes) < 2:
        LOGGER.warning("Analyze: need at least two scenes, got %d.", len(scenes))
        return 0.0, scenes

    two_most_recent = sorted(scenes, key=lambda s: s.datetime, reverse=True)[:2]
    recent, baseline = two_most_recent[0], two_most_recent[1]

    LOGGER.info("Analyze: comparing recent=%s baseline=%s", recent.id, baseline.id)
    recent_rgb = _load_demo_rgb(recent)
    baseline_rgb = _load_demo_rgb(baseline)
    score = change_score(baseline_rgb=baseline_rgb, recent_rgb=recent_rgb)
    LOGGER.info("Analyze: change_score=%0.4f", score)
    return score, [recent, baseline]


def deliver_alert(region: list[float], score: float, source_scenes: list[SceneSummary]) -> dict:
    """Deliver step: build and return final alert payload dictionary."""

    if score >= 0.30:
        threat_level = "high"
        recommended_action = "Escalate to emergency responders and monitor hourly."
    elif score >= 0.15:
        threat_level = "medium"
        recommended_action = "Request analyst review and increase observation cadence."
    else:
        threat_level = "low"
        recommended_action = "No immediate action required; continue routine monitoring."

    alert = {
        "region": region,
        "threat_level": threat_level,
        "score": round(score, 4),
        "recommended_action": recommended_action,
        "sources": [scene.id for scene in source_scenes],
    }
    LOGGER.info("Deliver: generated %s alert.", threat_level)
    return alert


def run_pipeline(bbox: list[float], start_date: str, end_date: str) -> dict:
    """Execute the full Watch -> Navigate -> Analyze -> Deliver pipeline."""

    trigger_source, fallback_scenes, no_trigger_reason = watch_for_trigger(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
    )
    if trigger_source is None:
        return {
            "region": bbox,
            "threat_level": "none",
            "score": 0.0,
            "recommended_action": no_trigger_reason or "No trigger found.",
            "sources": [],
        }

    scenes = navigate_to_scenes(bbox, start_date=start_date, end_date=end_date)
    score, compared = analyze_recent_change(scenes)
    if trigger_source == "stac":
        compared_ids = {scene.id for scene in compared}
        source_scenes = compared + [scene for scene in fallback_scenes if scene.id not in compared_ids]
        LOGGER.info("Deliver: including fallback STAC scene IDs in alert sources.")
    else:
        source_scenes = compared
    return deliver_alert(region=bbox, score=score, source_scenes=source_scenes)


def run_demo(bbox: list[float], start_date: str, end_date: str) -> dict:
    """Public helper used by demo script to execute one pipeline run."""

    return run_pipeline(bbox=bbox, start_date=start_date, end_date=end_date)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the agent skeleton."""

    parser = argparse.ArgumentParser(description="Aegis Atlas agent skeleton")
    parser.add_argument("--log-level", default="INFO", help="Logging level (e.g., INFO, DEBUG)")

    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Run the minimal agent pipeline")
    run_parser.add_argument(
        "--bbox",
        required=True,
        help='Bounding box string: "min_lon,min_lat,max_lon,max_lat"',
    )
    run_parser.add_argument("--start_date", required=True, help="Start date YYYY-MM-DD")
    run_parser.add_argument("--end_date", required=True, help="End date YYYY-MM-DD")
    return parser


def _parse_bbox_string(bbox_str: str) -> list[float]:
    """Parse a comma-separated bbox string into four float coordinates."""

    parts = [p.strip() for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError("--bbox must have exactly 4 comma-separated values")
    return [float(p) for p in parts]


def main() -> None:
    """CLI entrypoint."""

    args = build_parser().parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.command == "run":
        bbox = _parse_bbox_string(args.bbox)
        alert = run_pipeline(bbox=bbox, start_date=args.start_date, end_date=args.end_date)
        print(json.dumps(alert, indent=2))


if __name__ == "__main__":
    main()
