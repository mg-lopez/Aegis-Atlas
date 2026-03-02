"""Utility helpers for selecting Sentinel scenes from a STAC-like source."""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Tuple

Scene = Dict[str, object]


def _bboxes_overlap(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> bool:
    """Return True when two (min_lon, min_lat, max_lon, max_lat) boxes overlap."""
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def find_best_sentinel_scenes(
    bbox: Tuple[float, float, float, float],
    start_date: str,
    end_date: str,
) -> List[Scene]:
    """Return best Sentinel scenes in the given bbox/date window.

    This demo implementation uses a local in-memory catalog and returns matching
    scenes sorted by acquisition date descending.
    """
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    catalog: List[Scene] = [
        {
            "id": "S2A_DEMO_2025-01-10",
            "acquired": "2025-01-10",
            "bbox": (-74.2, 4.2, -73.6, 4.9),
            "signal": 0.21,
        },
        {
            "id": "S2B_DEMO_2025-01-17",
            "acquired": "2025-01-17",
            "bbox": (-74.0, 4.1, -73.5, 4.8),
            "signal": 0.74,
        },
        {
            "id": "S2B_DEMO_2025-02-02",
            "acquired": "2025-02-02",
            "bbox": (12.0, 41.7, 12.9, 42.4),
            "signal": 0.12,
        },
    ]

    matches = [
        s
        for s in catalog
        if start <= date.fromisoformat(str(s["acquired"])) <= end
        and _bboxes_overlap(bbox, tuple(s["bbox"]))
    ]
    return sorted(matches, key=lambda s: str(s["acquired"]), reverse=True)
