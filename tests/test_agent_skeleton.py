"""Unit tests for watch-stage fallback behavior in the agent pipeline."""

from __future__ import annotations

import agent_skeleton
import pytest
from stac_fetcher import SceneSummary


def _scene(scene_id: str, dt: str = "2024-08-01T00:00:00Z") -> SceneSummary:
    return SceneSummary(id=scene_id, datetime=dt, cloud_cover=10.0, assets={"B04": "https://example/B04.tif", "B08": "https://example/B08.tif"})


@pytest.fixture(autouse=True)
def _disable_external_network_signals(monkeypatch):
    monkeypatch.setattr(agent_skeleton, "_collect_external_signals", lambda *args, **kwargs: [])


def test_watch_for_trigger_uses_stac_soft_trigger_when_gdacs_empty(monkeypatch):
    monkeypatch.setattr(agent_skeleton, "poll_gdacs", lambda bbox: [])
    monkeypatch.setattr(
        agent_skeleton,
        "find_best_sentinel_scenes",
        lambda **kwargs: [_scene("stac-scene-1")],
    )

    trigger, fallback_scenes, reason = agent_skeleton.watch_for_trigger(
        bbox=[0, 0, 1, 1],
        start_date="2024-08-01",
        end_date="2024-08-31",
    )

    assert trigger == "stac"
    assert [scene.id for scene in fallback_scenes] == ["stac-scene-1"]
    assert reason is None


def test_watch_for_trigger_uses_max_cloud_80_for_stac_fallback(monkeypatch):
    monkeypatch.setattr(agent_skeleton, "poll_gdacs", lambda bbox: [])
    calls: list[dict] = []

    def fake_find_best_sentinel_scenes(**kwargs):
        calls.append(kwargs)
        return []

    monkeypatch.setattr(agent_skeleton, "find_best_sentinel_scenes", fake_find_best_sentinel_scenes)

    trigger, fallback_scenes, reason = agent_skeleton.watch_for_trigger(
        bbox=[0, 0, 1, 1],
        start_date="2024-08-01",
        end_date="2024-08-31",
    )

    assert trigger is None
    assert fallback_scenes == []
    assert reason == "No GDACS trigger and no Sentinel-2 scenes found for region/date range."
    assert calls[0]["max_cloud"] == 80.0


def test_run_pipeline_includes_fallback_scene_ids_in_sources(monkeypatch):
    monkeypatch.setattr(
        agent_skeleton,
        "watch_for_trigger",
        lambda **kwargs: ("stac", [_scene("fallback")], None),
    )
    monkeypatch.setattr(
        agent_skeleton,
        "navigate_to_scenes",
        lambda *args, **kwargs: [_scene("recent", "2024-08-03T00:00:00Z"), _scene("base")],
    )
    monkeypatch.setattr(agent_skeleton, "analyze_recent_change", lambda scenes, **kwargs: (0.2, scenes))

    alert = agent_skeleton.run_pipeline(
        bbox=[0, 0, 1, 1],
        start_date="2024-08-01",
        end_date="2024-08-31",
    )

    assert set(alert["sources"]) == {"recent", "base", "fallback"}


def test_run_pipeline_returns_none_only_when_no_gdacs_and_no_stac(monkeypatch):
    monkeypatch.setattr(
        agent_skeleton,
        "watch_for_trigger",
        lambda **kwargs: (
            None,
            [],
            "No GDACS trigger and no Sentinel-2 scenes found for region/date range.",
        ),
    )

    alert = agent_skeleton.run_pipeline(
        bbox=[0, 0, 1, 1],
        start_date="2024-08-01",
        end_date="2024-08-31",
    )

    assert alert["threat_level"] == "none"
    assert alert["recommended_action"] == (
        "No GDACS trigger and no Sentinel-2 scenes found for region/date range."
    )


def test_run_pipeline_use_sample_skips_stac_query(monkeypatch):
    monkeypatch.setattr(agent_skeleton, "watch_for_trigger", lambda **kwargs: (_ for _ in ()).throw(AssertionError("STAC path should be skipped")))
    monkeypatch.setattr(agent_skeleton, "analyze_sample_tiffs", lambda b, r: {"final_score": 0.75})

    alert = agent_skeleton.run_pipeline(
        bbox=[0, 0, 1, 1],
        start_date="2024-08-01",
        end_date="2024-08-31",
        use_sample=True,
    )

    assert alert["threat_level"] == "high"
    assert set(alert["sources"]) == {"sample_baseline.tif", "sample_recent.tif"}


def test_fuse_signals_emits_explainability_and_rationale():
    signals = [
        agent_skeleton.HazardSignal(
            key="sentinel_change",
            source="sentinel-2",
            hazard_type="surface-change",
            score=0.72,
            weight=0.55,
            status="ok",
            details="Synthetic satellite signal for test.",
        ),
        agent_skeleton.HazardSignal(
            key="gdacs",
            source="gdacs",
            hazard_type="global-alert",
            score=None,
            weight=0.25,
            status="no_event",
            details="No alert in AOI.",
        ),
    ]

    fused = agent_skeleton.fuse_signals(signals)

    assert fused["threat_level"] == "high"
    assert fused["confidence"] in {"low", "medium", "high"}
    assert fused["rationale"]
    assert "signals" in fused["explainability"]
    assert fused["explainability"]["signals"][0]["key"] == "sentinel_change"


def test_run_pipeline_includes_phase3_payload_fields(monkeypatch):
    monkeypatch.setattr(
        agent_skeleton,
        "watch_for_trigger",
        lambda **kwargs: ("stac", [_scene("fallback")], None),
    )
    monkeypatch.setattr(
        agent_skeleton,
        "navigate_to_scenes",
        lambda *args, **kwargs: [_scene("recent", "2024-08-03T00:00:00Z"), _scene("base")],
    )
    monkeypatch.setattr(agent_skeleton, "analyze_recent_change", lambda scenes, **kwargs: (0.5, scenes))
    monkeypatch.setattr(
        agent_skeleton,
        "_collect_external_signals",
        lambda *args, **kwargs: [
            agent_skeleton.HazardSignal(
                key="gdacs",
                source="gdacs-demo",
                hazard_type="wildfire",
                score=0.78,
                weight=0.25,
                status="ok",
                details="Demo overlap",
            )
        ],
    )

    alert = agent_skeleton.run_pipeline(
        bbox=[0, 0, 1, 1],
        start_date="2024-08-01",
        end_date="2024-08-31",
    )

    assert "rationale" in alert
    assert "explainability" in alert
    assert "confidence" in alert


def test_run_pipeline_live_fast_uses_stac_metadata_and_skips_heavy_analysis(monkeypatch):
    monkeypatch.setattr(
        agent_skeleton,
        "watch_for_trigger",
        lambda **kwargs: ("stac", [_scene("fallback", "2024-08-03T00:00:00Z")], None),
    )
    monkeypatch.setattr(
        agent_skeleton,
        "navigate_to_scenes",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("navigate_to_scenes should be skipped in fast live mode")),
    )
    monkeypatch.setattr(
        agent_skeleton,
        "_collect_external_signals",
        lambda *args, **kwargs: [],
    )

    alert = agent_skeleton.run_pipeline(
        bbox=[0, 0, 1, 1],
        start_date="2024-08-01",
        end_date="2024-08-31",
        use_live_fast=True,
    )

    assert alert["threat_level"] in {"low", "medium", "high", "none"}
    assert alert["sources"] == ["fallback"]
    assert any("Fast-mode estimate from STAC metadata" in r for r in alert["rationale"])


def test_geo_context_signal_varies_by_location():
    low_signal = agent_skeleton._signal_from_geo_context([-0.2, 51.4, 0.1, 51.7])  # London
    high_signal = agent_skeleton._signal_from_geo_context([30.0, 48.0, 32.0, 49.0])  # Ukraine zone

    assert low_signal.score is None or low_signal.score < 0.3
    assert high_signal.score is not None
    assert high_signal.score > 0.5
