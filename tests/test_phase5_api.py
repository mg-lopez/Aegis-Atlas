"""Phase 5 API tests: notifications, watchlists, and history persistence."""

from __future__ import annotations

import history_store
import notifications
import watchlists
import webapp


def _configure_temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(history_store, "HISTORY_FILE", tmp_path / "alert_history.jsonl")
    monkeypatch.setattr(watchlists, "WATCHLISTS_FILE", tmp_path / "watchlists.json")


def test_analyze_persists_history_and_returns_history_id(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    monkeypatch.setattr(
        webapp,
        "run_pipeline",
        lambda **kwargs: {
            "threat_level": "medium",
            "score": 0.5,
            "confidence": "medium",
            "recommended_action": "Prepare to evacuate.",
            "sources": ["scene-1"],
            "rationale": ["test rationale"],
            "explainability": {"signals": []},
        },
    )

    client = webapp.app.test_client()
    response = client.post("/api/analyze", json={"lat": 35.0, "lon": -120.0, "mode": "sample"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["history_id"]
    assert "notifications" in payload

    history_response = client.get("/api/history?limit=5")
    assert history_response.status_code == 200
    history_payload = history_response.get_json()
    assert history_payload["ok"] is True
    assert history_payload["items"]
    assert history_payload["items"][0]["type"] == "single_analysis"


def test_watchlist_create_list_and_scan(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    monkeypatch.setattr(
        webapp,
        "run_pipeline",
        lambda **kwargs: {
            "threat_level": "low",
            "score": 0.1,
            "confidence": "low",
            "recommended_action": "Monitor.",
            "sources": [],
            "rationale": [],
            "explainability": {"signals": []},
        },
    )

    client = webapp.app.test_client()
    create_response = client.post(
        "/api/watchlists",
        json={
            "name": "Family",
            "members": [
                {"label": "Home", "lat": 34.1, "lon": -118.2},
                {"label": "School", "lat": 34.2, "lon": -118.3},
            ],
        },
    )
    assert create_response.status_code == 201
    watchlist = create_response.get_json()["watchlist"]
    watchlist_id = watchlist["id"]

    list_response = client.get("/api/watchlists")
    assert list_response.status_code == 200
    items = list_response.get_json()["items"]
    assert len(items) == 1

    scan_response = client.post(f"/api/watchlists/{watchlist_id}/scan", json={"mode": "sample"})
    assert scan_response.status_code == 200
    scan_payload = scan_response.get_json()
    assert scan_payload["ok"] is True
    assert len(scan_payload["results"]) == 2
    assert scan_payload["history_id"]


def test_watchlist_rejects_excessive_members(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    client = webapp.app.test_client()
    members = [{"label": f"m{i}", "lat": 1.0, "lon": 2.0} for i in range(26)]
    response = client.post("/api/watchlists", json={"name": "Too Many", "members": members})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["ok"] is False
    assert "cannot exceed 25" in payload["error"]


def test_watchlist_rejects_invalid_member_payload(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    client = webapp.app.test_client()
    response = client.post(
        "/api/watchlists",
        json={"name": "Bad", "members": [{"label": "bad", "lat": "oops", "lon": 2.0}]},
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["ok"] is False
    assert "Invalid numeric value for lat" in payload["error"]


def test_scan_watchlist_handles_member_level_pipeline_failures(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    state = {"count": 0}

    def flaky_pipeline(**kwargs):
        state["count"] += 1
        if state["count"] == 1:
            raise RuntimeError("upstream timeout")
        return {
            "threat_level": "medium",
            "score": 0.42,
            "confidence": "medium",
            "recommended_action": "Prepare.",
            "sources": [],
            "rationale": [],
            "explainability": {"signals": []},
        }

    monkeypatch.setattr(webapp, "run_pipeline", flaky_pipeline)
    client = webapp.app.test_client()
    create_response = client.post(
        "/api/watchlists",
        json={
            "name": "Family",
            "members": [
                {"label": "A", "lat": 1.0, "lon": 1.0},
                {"label": "B", "lat": 2.0, "lon": 2.0},
            ],
        },
    )
    watchlist_id = create_response.get_json()["watchlist"]["id"]

    scan_response = client.post(f"/api/watchlists/{watchlist_id}/scan", json={"mode": "sample"})
    assert scan_response.status_code == 200
    payload = scan_response.get_json()
    assert payload["ok"] is True
    assert len(payload["results"]) == 2
    assert payload["results"][0]["ok"] is False
    assert "error" in payload["results"][0]
    assert payload["results"][1]["ok"] is True


def test_scan_watchlist_not_found_returns_404(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    client = webapp.app.test_client()
    response = client.post("/api/watchlists/not-found/scan", json={"mode": "sample"})
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["ok"] is False
    assert "not found" in payload["error"]


def test_notification_policy_skips_low_threat():
    events = notifications.notify_alert({"threat_level": "low", "score": 0.12})
    assert events[0]["status"] == "skipped"
    assert events[0]["reason"] == "threat_below_threshold"
