"""Run one demo alert and persist it to ``demo/last_alert.json``.

Usage:
    python demo/run_demo.py

Optional arguments:
    --bbox "min_lon,min_lat,max_lon,max_lat"
    --start-date YYYY-MM-DD
    --end-date YYYY-MM-DD
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_skeleton import run_demo


DEFAULT_BBOX = [-122.65, 38.20, -122.10, 38.65]
DEFAULT_START_DATE = "2024-08-01"
DEFAULT_END_DATE = "2024-08-31"
OUTPUT_PATH = Path(__file__).resolve().parent / "last_alert.json"


def _parse_bbox(value: str) -> list[float]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bbox must contain 4 comma-separated floats")
    try:
        return [float(part) for part in parts]
    except ValueError as exc:  # pragma: no cover - argparse handles display
        raise argparse.ArgumentTypeError("bbox values must be valid floats") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Aegis Atlas demo and write last_alert.json")
    parser.add_argument("--bbox", type=_parse_bbox, default=DEFAULT_BBOX)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    alert = run_demo(bbox=args.bbox, start_date=args.start_date, end_date=args.end_date)

    OUTPUT_PATH.write_text(json.dumps(alert, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(alert, indent=2))
    print(f"\nWrote alert payload to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
