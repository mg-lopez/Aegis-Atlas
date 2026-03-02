"""Minimal Watch -> Navigate -> Analyze -> Deliver loop for disaster monitoring."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Dict, List, Tuple

from stac_fetcher import find_best_sentinel_scenes

LOGGER = logging.getLogger(__name__)
BBox = Tuple[float, float, float, float]


def parse_bbox(bbox_str: str) -> BBox:
    """Parse a bbox string as min_lon,min_lat,max_lon,max_lat."""
    parts = [float(p.strip()) for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must contain 4 comma-separated values")
    min_lon, min_lat, max_lon, max_lat = parts
    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValueError("bbox min values must be less than max values")
    return min_lon, min_lat, max_lon, max_lat


def _bboxes_overlap(a: BBox, b: BBox) -> bool:
    """Return True when two geographic bounding boxes overlap."""
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def poll_gdacs(region: BBox) -> List[Dict[str, object]]:
    """Poll GDACS for active alerts.

    Demo placeholder: emits one hardcoded trigger when the requested region
    overlaps a demo region in northern South America.
    """
    demo_region = (-74.5, 3.8, -73.2, 5.2)
    if _bboxes_overlap(region, demo_region):
        return [
            {
                "event_id": "gdacs-demo-001",
                "hazard": "flood",
                "severity": "medium",
                "region": region,
            }
        ]
    return []


def navigate_scenes(region: BBox, start_date: str, end_date: str) -> List[Dict[str, object]]:
    """Find Sentinel scenes relevant to the region/date request."""
    LOGGER.info("Navigating STAC scenes for region=%s, start=%s, end=%s", region, start_date, end_date)
    return find_best_sentinel_scenes(region, start_date, end_date)


def analyze_change(scenes: List[Dict[str, object]]) -> Tuple[float, List[Dict[str, object]]]:
    """Compute a change score using the two most recent scenes.

    Returns:
        (change_score, selected_scenes)
    """
    if len(scenes) < 2:
        raise ValueError("Need at least two scenes to analyze change")

    selected = scenes[:2]
    score = abs(float(selected[0]["signal"]) - float(selected[1]["signal"]))
    LOGGER.info("Computed change score %.3f from scenes %s and %s", score, selected[0]["id"], selected[1]["id"])
    return score, selected


def _threat_level(score: float) -> str:
    """Map score to a threat level."""
    if score >= 0.6:
        return "critical"
    if score >= 0.35:
        return "high"
    if score >= 0.15:
        return "medium"
    return "low"


def deliver_alert(region: BBox, score: float, selected_scenes: List[Dict[str, object]]) -> Dict[str, object]:
    """Build and print the final alert payload."""
    threat = _threat_level(score)
    action = {
        "critical": "Escalate immediately to emergency responders.",
        "high": "Issue incident watch and schedule rapid reassessment.",
        "medium": "Continue monitoring and validate with on-ground reports.",
        "low": "No immediate action; keep routine observation.",
    }[threat]

    alert = {
        "region": region,
        "threat_level": threat,
        "score": round(score, 3),
        "recommended_action": action,
        "sources": [str(s["id"]) for s in selected_scenes],
    }
    print(alert)
    return alert


def run_loop(bbox: BBox, start_date: str, end_date: str) -> Dict[str, object]:
    """Execute Watch -> Navigate -> Analyze -> Deliver for a single region."""
    LOGGER.info("Watch step: polling GDACS")
    events = poll_gdacs(bbox)
    if not events:
        LOGGER.info("No GDACS trigger for region=%s", bbox)
        return {
            "region": bbox,
            "threat_level": "none",
            "score": 0.0,
            "recommended_action": "No trigger found in watch step.",
            "sources": [],
        }

    LOGGER.info("Navigate step: %d trigger(s) found", len(events))
    scenes = navigate_scenes(bbox, start_date, end_date)
    score, selected = analyze_change(scenes)
    return deliver_alert(bbox, score, selected)


def _build_parser() -> argparse.ArgumentParser:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(description="Minimal geospatial agent loop")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run watch->navigate->analyze->deliver")
    run_parser.add_argument("--bbox", required=True, help="min_lon,min_lat,max_lon,max_lat")
    run_parser.add_argument("--start_date", required=True, help="YYYY-MM-DD")
    run_parser.add_argument("--end_date", required=True, help="YYYY-MM-DD")

    return parser


def _normalize_argv(argv: List[str]) -> List[str]:
    """Normalize argv so `--bbox "-x,y,..."` is accepted with negative longitudes."""
    normalized = list(argv)
    if "--bbox" in normalized:
        idx = normalized.index("--bbox")
        if idx + 1 < len(normalized) and normalized[idx + 1].startswith("-"):
            normalized[idx] = f"--bbox={normalized[idx + 1]}"
            del normalized[idx + 1]
    return normalized


def main() -> None:
    """CLI entrypoint."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = _build_parser()
    args = parser.parse_args(_normalize_argv(sys.argv[1:]))

    if args.command == "run":
        bbox = parse_bbox(args.bbox)
        run_loop(bbox, args.start_date, args.end_date)


if __name__ == "__main__":
    main()
