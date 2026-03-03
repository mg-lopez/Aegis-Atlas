"""Unit tests for watch-stage fallback behavior in the agent pipeline."""

from __future__ import annotations

import agent_skeleton
from stac_fetcher import SceneSummary


def _scene(scene_id: str, dt: str = "2024-08-01T00:00:00Z") -> SceneSummary:
    return SceneSummary(id=scene_id, datetime=dt, cloud_cover=10.0, assets=["B04", "B08"])


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
    monkeypatch.setattr(agent_skeleton, "analyze_recent_change", lambda scenes: (0.2, scenes))

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
