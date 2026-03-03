"""Integration test for deterministic sample analysis mode."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_sample_mode_reports_high_threat():
    result = subprocess.run(
        ["python", "demo/run_demo.py", "--use-sample"],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    root = Path(__file__).resolve().parents[1]
    metrics = json.loads((Path("/app/demo/debug") / "metrics.json").read_text(encoding="utf-8"))
    alert = json.loads((root / "demo" / "last_alert.json").read_text(encoding="utf-8"))

    assert metrics["final_score"] >= 0.6
    assert alert["threat_level"] == "high"
