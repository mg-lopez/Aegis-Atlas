"""Minimal Watch -> Navigate -> Analyze -> Deliver agent skeleton with CLI."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

import numpy as np

from analyze import detect_change_from_band_difference
from stac_fetcher import SceneSummary, find_best_sentinel_scenes


@dataclass
class HazardSignal:
    """Represents a watched hazard signal for a target geography."""

    hazard_type: str
    confidence: float
    bbox: list[float]


@dataclass
class AlertPayload:
    """Final alert payload emitted by the pipeline."""

    status: str
    message: str
    hazard_type: str
    confidence: float
    bbox: list[float]
    candidate_scenes: list[dict]
    analysis: dict


class AegisAtlasAgent:
    """Reference implementation of a lightweight disaster-intel pipeline."""

    def watch(self, bbox: list[float], hazard_type: str = "wildfire") -> HazardSignal:
        """Watch step: receive hazard signal (placeholder for feed ingestion)."""

        return HazardSignal(hazard_type=hazard_type, confidence=0.7, bbox=bbox)

    def navigate(self, signal: HazardSignal, start_date: str, end_date: str, max_cloud: float) -> list[SceneSummary]:
        """Navigate step: resolve the best relevant Sentinel-2 scenes via STAC."""

        return find_best_sentinel_scenes(
            bbox=signal.bbox,
            start_date=start_date,
            end_date=end_date,
            max_cloud=max_cloud,
        )

    def analyze(self, scenes: list[SceneSummary]) -> dict:
        """Analyze step: run simple placeholder change analysis."""

        if len(scenes) < 2:
            return {"change_score": 0.0, "alert": False, "reason": "insufficient_scenes"}

        rng = np.random.default_rng(seed=7)
        before = rng.random((128, 128), dtype=np.float32)
        after = rng.random((128, 128), dtype=np.float32)
        return detect_change_from_band_difference(before, after, change_threshold=0.18)

    def deliver(self, signal: HazardSignal, scenes: list[SceneSummary], analysis_result: dict) -> AlertPayload:
        """Deliver step: produce action-oriented alert payload."""

        alert_flag = bool(analysis_result.get("alert", False))
        status = "ALERT" if alert_flag else "MONITOR"
        message = (
            "Potential hazard-driven surface change detected; notify registered contacts."
            if alert_flag
            else "No significant change detected; continue monitoring."
        )
        return AlertPayload(
            status=status,
            message=message,
            hazard_type=signal.hazard_type,
            confidence=signal.confidence,
            bbox=signal.bbox,
            candidate_scenes=[asdict(scene) for scene in scenes],
            analysis=analysis_result,
        )


def build_parser() -> argparse.ArgumentParser:
    """Build command-line parser for running the prototype pipeline."""

    parser = argparse.ArgumentParser(description="Aegis Atlas prototype pipeline")
    parser.add_argument("--bbox", nargs=4, type=float, required=True, metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"))
    parser.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--max-cloud", type=float, default=20.0)
    parser.add_argument("--hazard-type", default="wildfire")
    return parser


def main() -> None:
    """Run end-to-end pipeline from CLI arguments and print alert JSON."""

    args = build_parser().parse_args()
    agent = AegisAtlasAgent()

    signal = agent.watch(bbox=args.bbox, hazard_type=args.hazard_type)
    scenes = agent.navigate(signal=signal, start_date=args.start_date, end_date=args.end_date, max_cloud=args.max_cloud)
    analysis_result = agent.analyze(scenes)
    payload = agent.deliver(signal, scenes, analysis_result)

    print(json.dumps(asdict(payload), indent=2))


if __name__ == "__main__":
    main()
