"""Minimal Watch -> Navigate -> Analyze -> Deliver agent skeleton with CLI."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


from analyze import analyze_sample_tiffs, analyze_scene_pair
from stac_fetcher import SceneSummary, find_best_sentinel_scenes, scene_to_dict

LOGGER = logging.getLogger(__name__)
DEBUG_DIR = Path("/app/demo/debug")

DEMO_TRIGGER_BBOX = (-119.5, 33.5, -117.0, 35.2)


@dataclass(frozen=True)
class HazardEvent:
    region: list[float]
    hazard_type: str
    source: str


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


def deliver_alert(
    region: list[float],
    score: float | None,
    source_scenes: list[SceneSummary],
    no_baseline: bool = False,
) -> dict:
    if score is None and no_baseline:
        threat_level = "low"
        recommended_action = "Monitor and corroborate; insufficient imagery for automated decision."
    elif score is not None and score >= 0.6:
        threat_level = "high"
        recommended_action = "Immediate evacuation advised; verify with authorities and proceed to nearest safe zone."
    elif score is not None and score >= 0.3:
        threat_level = "medium"
        recommended_action = "Prepare to evacuate; monitor updates and assemble emergency kit."
    else:
        threat_level = "low"
        recommended_action = "No immediate action required; continue monitoring."

    return {
        "region": region,
        "threat_level": threat_level,
        "score": None if score is None else round(score, 4),
        "recommended_action": recommended_action,
        "sources": [scene.id for scene in source_scenes],
    }


def run_pipeline(bbox: list[float], start_date: str, end_date: str, use_sample: bool = False) -> dict:
    if use_sample:
        from demo.generate_sample_tiffs import generate_sample_tiffs

        baseline_path, recent_path = generate_sample_tiffs()
        metrics = analyze_sample_tiffs(baseline_path, recent_path)
        sample_scenes = [
            SceneSummary(id=baseline_path.name, datetime=start_date, cloud_cover=0.0, assets={}),
            SceneSummary(id=recent_path.name, datetime=end_date, cloud_cover=0.0, assets={}),
        ]
        return deliver_alert(region=bbox, score=float(metrics["final_score"]), source_scenes=sample_scenes)

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
    score, compared = analyze_recent_change(scenes, bbox=bbox, start_date=start_date, end_date=end_date)
    if trigger_source == "stac":
        compared_ids = {scene.id for scene in compared}
        source_scenes = compared + [scene for scene in fallback_scenes if scene.id not in compared_ids]
    else:
        source_scenes = compared
    return deliver_alert(region=bbox, score=score, source_scenes=source_scenes, no_baseline=score is None)


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
        alert = run_pipeline(bbox=bbox, start_date=args.start_date, end_date=args.end_date)
        print(json.dumps(alert, indent=2))


if __name__ == "__main__":
    main()
