"""Run scripted low/medium/high scenarios and save presentation snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from demo.scenarios import SCENARIOS, build_scenario_alert, snapshot_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic Aegis Atlas demo scenarios")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=sorted(SCENARIOS.keys()),
        help="Scenario(s) to run; defaults to all.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    names = args.scenario or ["low", "medium", "high"]

    snapshots_dir, debug_report_path = snapshot_paths(PROJECT_ROOT)
    summary: dict[str, object] = {
        "scenarios": [],
        "generated_files": [],
    }

    for name in names:
        scenario = SCENARIOS[name]
        alert = build_scenario_alert(scenario)
        out_path = snapshots_dir / f"{name}.json"
        out_path.write_text(json.dumps(alert, indent=2) + "\n", encoding="utf-8")

        row = {
            "name": name,
            "expected_threat_level": scenario.expected_threat_level,
            "actual_threat_level": alert["threat_level"],
            "score": alert["score"],
            "confidence": alert["confidence"],
            "snapshot_file": str(out_path.relative_to(PROJECT_ROOT)),
        }
        summary["scenarios"].append(row)
        summary["generated_files"].append(str(out_path.relative_to(PROJECT_ROOT)))

    summary_path = snapshots_dir / "summary.json"
    summary["generated_files"].append(str(summary_path.relative_to(PROJECT_ROOT)))
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    debug_report_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"\nWrote snapshots to {snapshots_dir}")
    print(f"Wrote fusion report to {debug_report_path}")


if __name__ == "__main__":
    main()
