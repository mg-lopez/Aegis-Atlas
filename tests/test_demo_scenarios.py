"""Calibration tests for deterministic demo scenarios."""

from __future__ import annotations

from demo.scenarios import SCENARIOS, build_scenario_alert


def test_demo_scenarios_match_expected_threat_levels():
    for name in ("low", "medium", "high"):
        scenario = SCENARIOS[name]
        alert = build_scenario_alert(scenario)
        assert alert["threat_level"] == scenario.expected_threat_level


def test_high_scenario_has_multiple_active_signals():
    alert = build_scenario_alert(SCENARIOS["high"])
    explainability = alert["explainability"]
    assert explainability["active_signal_count"] >= 2
    assert alert["confidence"] in {"medium", "high"}
