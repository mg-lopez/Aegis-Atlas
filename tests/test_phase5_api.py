"""Phase 5 API tests: notifications, watchlists, and history persistence."""

from __future__ import annotations

import history_store
import incident_store
import notifications
import watchlists
import webapp


def _configure_temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(history_store, "HISTORY_FILE", tmp_path / "alert_history.jsonl")
    monkeypatch.setattr(incident_store, "INCIDENTS_FILE", tmp_path / "incidents.json")
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
    assert history_payload["items"][0]["analysis_key"]
    assert history_payload["items"][0]["query"]["lens"] == "general"


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
    assert scan_payload["summary"]["average_score"] == 0.1
    assert scan_payload["summary"]["top_hotspot"]["member_label"] in {"Home", "School"}
    assert scan_payload["summary"]["health_note"]


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


def test_map_layers_endpoint_aggregates_analysis_watchlists_incidents(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    monkeypatch.setattr(
        webapp,
        "run_pipeline",
        lambda **kwargs: {
            "threat_level": "high",
            "score": 0.81,
            "confidence": "high",
            "recommended_action": "Escalate.",
            "sources": ["scene-1"],
            "rationale": ["map-layer test"],
            "explainability": {
                "coverage": 0.78,
                "consensus": 0.69,
                "signals": [
                    {
                        "key": "geo_conflict",
                        "source": "regional-risk",
                        "hazard_type": "geopolitical-composite",
                        "status": "ok",
                        "score": 0.81,
                        "weight": 0.4,
                        "contribution": 0.324,
                        "reliability": 1.0,
                        "details": "Conflict corridor active.",
                    }
                ],
            },
        },
    )

    client = webapp.app.test_client()
    analysis_response = client.post(
        "/api/analyze",
        json={"lat": 31.5, "lon": 34.8, "mode": "sample", "lens": "security"},
    )
    assert analysis_response.status_code == 200
    history_id = analysis_response.get_json()["history_id"]

    incident_response = client.post("/api/incidents", json={"history_id": history_id})
    assert incident_response.status_code == 201

    create_watchlist = client.post(
        "/api/watchlists",
        json={
            "name": "Forward Sites",
            "members": [
                {"label": "Site Alpha", "lat": 31.55, "lon": 34.82},
                {"label": "Site Bravo", "lat": 31.62, "lon": 34.91},
            ],
        },
    )
    assert create_watchlist.status_code == 201
    watchlist_id = create_watchlist.get_json()["watchlist"]["id"]

    scan_response = client.post(
        f"/api/watchlists/{watchlist_id}/scan",
        json={"mode": "sample", "lens": "security"},
    )
    assert scan_response.status_code == 200

    map_response = client.get("/api/map/layers?lens=security")
    assert map_response.status_code == 200
    payload = map_response.get_json()
    assert payload["ok"] is True
    assert payload["lens"] == "security"
    assert payload["heatmap_points"]
    assert payload["hotspot_markers"]
    assert payload["incident_markers"]
    assert payload["watchlist_markers"]
    assert payload["instability_points"]
    assert payload["counts"]["incident_markers"] == 1
    assert payload["counts"]["watchlist_markers"] == 2


def test_map_layers_seed_demo_hotspots_when_workspace_is_empty(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    client = webapp.app.test_client()

    map_response = client.get("/api/map/layers?lens=logistics")
    assert map_response.status_code == 200
    payload = map_response.get_json()
    assert payload["ok"] is True
    assert payload["heatmap_points"]
    assert payload["hotspot_markers"]
    assert payload["counts"]["incident_markers"] == 0
    assert payload["counts"]["watchlist_markers"] == 0
    assert payload["hotspot_markers"][0]["source_type"] == "preset"

    overview_response = client.get("/api/dashboard/overview?lens=logistics")
    assert overview_response.status_code == 200
    overview_payload = overview_response.get_json()
    assert overview_payload["counts"]["hotspots"] >= 1
    assert overview_payload["recent_bulletins"]


def test_live_context_endpoints_return_overview_bulletins_and_instability(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    monkeypatch.setattr(
        webapp,
        "run_pipeline",
        lambda **kwargs: {
            "threat_level": "high",
            "score": 0.74,
            "confidence": "high",
            "recommended_action": "Escalate.",
            "sources": ["scene-1"],
            "rationale": ["live-context test"],
            "explainability": {
                "coverage": 0.72,
                "consensus": 0.68,
                "signals": [
                    {
                        "key": "geo_conflict",
                        "source": "regional-risk",
                        "hazard_type": "geopolitical-composite",
                        "status": "ok",
                        "score": 0.74,
                        "weight": 0.4,
                        "contribution": 0.296,
                        "reliability": 1.0,
                        "details": "Escalation corridor active.",
                    },
                    {
                        "key": "headline_conflict",
                        "source": "gdelt",
                        "hazard_type": "headline-cluster",
                        "status": "ok",
                        "score": 0.66,
                        "weight": 0.2,
                        "contribution": 0.132,
                        "reliability": 1.0,
                        "details": "Israel: 6 recent conflict-related headlines in 7-day window (fresh cache).",
                    },
                ],
            },
        },
    )

    client = webapp.app.test_client()
    analysis_response = client.post(
        "/api/analyze",
        json={"lat": 31.5, "lon": 34.8, "mode": "live", "lens": "security"},
    )
    history_id = analysis_response.get_json()["history_id"]
    client.post("/api/incidents", json={"history_id": history_id})

    overview = client.get("/api/dashboard/overview?lens=security")
    assert overview.status_code == 200
    overview_payload = overview.get_json()
    assert overview_payload["ok"] is True
    assert overview_payload["counts"]["open_incidents"] == 1
    assert overview_payload["recent_bulletins"]
    assert overview_payload["instability_summary"]
    assert "system_note" in overview_payload

    bulletins = client.get("/api/feed/bulletins?lens=security&limit=5")
    assert bulletins.status_code == 200
    bulletins_payload = bulletins.get_json()
    assert bulletins_payload["ok"] is True
    assert bulletins_payload["items"]
    assert bulletins_payload["items"][0]["title"]
    assert any(item["kind"] == "news" for item in bulletins_payload["items"])
    assert any(item["source"] == "gdelt" for item in bulletins_payload["items"])

    instability = client.get("/api/instability?lens=security&limit=5")
    assert instability.status_code == 200
    instability_payload = instability.get_json()
    assert instability_payload["ok"] is True
    assert instability_payload["items"]
    assert instability_payload["top_item"]["name"]


def test_notification_policy_skips_low_threat():
    events = notifications.notify_alert({"threat_level": "low", "score": 0.12})
    assert events[0]["status"] == "skipped"
    assert events[0]["reason"] == "threat_below_threshold"


def test_trends_endpoint_reports_rising_signal(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    scores = iter([0.22, 0.46])

    def stub_pipeline(**kwargs):
        return {
            "threat_level": "low" if kwargs["use_sample"] else "medium",
            "score": next(scores),
            "confidence": "medium",
            "recommended_action": "Monitor.",
            "sources": ["scene-1"],
            "rationale": ["trend test"],
            "explainability": {
                "coverage": 0.7,
                "consensus": 0.6,
                "signals": [
                    {
                        "key": "sentinel_change",
                        "source": "sentinel-2",
                        "hazard_type": "surface-change",
                        "status": "ok",
                        "score": 0.4,
                        "weight": 0.35,
                        "contribution": 0.14,
                        "reliability": 1.0,
                        "details": "Synthetic signal.",
                    }
                ],
            },
        }

    monkeypatch.setattr(webapp, "run_pipeline", stub_pipeline)
    client = webapp.app.test_client()
    client.post("/api/analyze", json={"lat": 35.0, "lon": -120.0, "mode": "sample"})
    client.post("/api/analyze", json={"lat": 35.0, "lon": -120.0, "mode": "sample"})

    response = client.get(
        "/api/trends?lat=35.0&lon=-120.0&radius_km=25&mode=sample&risk_profile=balanced"
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["trend"]["point_count"] == 2
    assert payload["trend"]["trend_label"] == "rising"
    assert payload["trend"]["delta_score"] == 0.24


def test_watchlist_trends_identify_biggest_riser(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    responses = iter(
        [
            {"threat_level": "low", "score": 0.10},
            {"threat_level": "low", "score": 0.12},
            {"threat_level": "high", "score": 0.55},
            {"threat_level": "low", "score": 0.14},
        ]
    )

    def stub_pipeline(**kwargs):
        item = next(responses)
        return {
            **item,
            "confidence": "medium",
            "recommended_action": "Monitor.",
            "sources": [],
            "rationale": [],
            "explainability": {
                "coverage": 0.7,
                "consensus": 0.6,
                "signals": [
                    {
                        "key": "sentinel_change",
                        "source": "sentinel-2",
                        "hazard_type": "surface-change",
                        "status": "ok",
                        "score": item["score"],
                        "weight": 0.35,
                        "contribution": 0.14,
                        "reliability": 1.0,
                        "details": "Synthetic signal.",
                    }
                ],
            },
        }

    monkeypatch.setattr(webapp, "run_pipeline", stub_pipeline)
    client = webapp.app.test_client()
    create_response = client.post(
        "/api/watchlists",
        json={
            "name": "Facilities",
            "members": [
                {"label": "Alpha", "lat": 1.0, "lon": 1.0},
                {"label": "Bravo", "lat": 2.0, "lon": 2.0},
            ],
        },
    )
    watchlist_id = create_response.get_json()["watchlist"]["id"]

    client.post(f"/api/watchlists/{watchlist_id}/scan", json={"mode": "sample"})
    client.post(f"/api/watchlists/{watchlist_id}/scan", json={"mode": "sample"})

    response = client.get(f"/api/watchlists/{watchlist_id}/trends")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["trends"]["biggest_riser"]["member_label"] == "Alpha"
    assert payload["trends"]["newly_elevated"]["member_label"] == "Alpha"


def test_watchlist_trends_are_filtered_by_lens(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    responses = iter(
        [
            {"threat_level": "low", "score": 0.12},
            {"threat_level": "low", "score": 0.12},
            {"threat_level": "high", "score": 0.52},
            {"threat_level": "low", "score": 0.15},
        ]
    )

    def stub_pipeline(**kwargs):
        item = next(responses)
        return {
            **item,
            "confidence": "medium",
            "recommended_action": "Monitor.",
            "sources": [],
            "rationale": [],
            "explainability": {
                "coverage": 0.7,
                "consensus": 0.6,
                "signals": [
                    {
                        "key": "geo_conflict",
                        "source": "regional-risk",
                        "hazard_type": "geopolitical-composite",
                        "status": "ok",
                        "score": item["score"],
                        "weight": 0.4,
                        "effective_weight": 0.4,
                        "reliability": 1.0,
                        "contribution": 0.16,
                        "details": "Synthetic signal.",
                    }
                ],
            },
        }

    monkeypatch.setattr(webapp, "run_pipeline", stub_pipeline)
    client = webapp.app.test_client()
    create_response = client.post(
        "/api/watchlists",
        json={
            "name": "Facilities",
            "members": [
                {"label": "Alpha", "lat": 1.0, "lon": 1.0},
                {"label": "Bravo", "lat": 2.0, "lon": 2.0},
            ],
        },
    )
    watchlist_id = create_response.get_json()["watchlist"]["id"]

    client.post(f"/api/watchlists/{watchlist_id}/scan", json={"mode": "sample", "lens": "general"})
    client.post(f"/api/watchlists/{watchlist_id}/scan", json={"mode": "sample", "lens": "security"})

    response = client.get(f"/api/watchlists/{watchlist_id}/trends?lens=general")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["lens"] == "general"
    assert payload["trends"]["biggest_riser"] is None


def test_analysis_returns_open_incident_context_for_matching_analysis(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    monkeypatch.setattr(
        webapp,
        "run_pipeline",
        lambda **kwargs: {
            "threat_level": "high",
            "score": 0.63,
            "confidence": "high",
            "confidence_score": 0.79,
            "recommended_action": "Escalate immediately.",
            "sources": ["scene-9"],
            "rationale": ["incident-linked rationale"],
            "explainability": {
                "coverage": 0.82,
                "consensus": 0.74,
                "signals": [
                    {
                        "key": "geo_conflict",
                        "source": "regional-risk",
                        "hazard_type": "geopolitical-composite",
                        "status": "ok",
                        "score": 0.63,
                        "weight": 0.4,
                        "effective_weight": 0.4,
                        "reliability": 1.0,
                        "contribution": 0.252,
                        "details": "Synthetic escalation signal.",
                    }
                ],
            },
        },
    )

    client = webapp.app.test_client()
    first_response = client.post(
        "/api/analyze",
        json={"lat": 32.0853, "lon": 34.7818, "mode": "sample", "lens": "security"},
    )
    assert first_response.status_code == 200
    first_payload = first_response.get_json()

    create_incident_response = client.post("/api/incidents", json={"history_id": first_payload["history_id"]})
    assert create_incident_response.status_code == 201
    incident = create_incident_response.get_json()["incident"]

    second_response = client.post(
        "/api/analyze",
        json={"lat": 32.0853, "lon": 34.7818, "mode": "sample", "lens": "security"},
    )
    assert second_response.status_code == 200
    second_payload = second_response.get_json()
    assert second_payload["incident_context"]["id"] == incident["id"]
    assert second_payload["incident_context"]["status"] == "open"
    assert second_payload["incident_context"]["location_label"]


def test_incident_queue_lifecycle(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)
    scores = iter([0.36, 0.59])

    def stub_pipeline(**kwargs):
        score = next(scores)
        threat = "medium" if score < 0.5 else "high"
        return {
            "threat_level": threat,
            "score": score,
            "confidence": "medium" if threat == "medium" else "high",
            "confidence_score": 0.62 if threat == "medium" else 0.78,
            "recommended_action": "Escalate." if threat == "high" else "Monitor.",
            "sources": ["scene-1"],
            "source_details": [
                {"id": "scene-1", "datetime": "2026-03-06T12:00:00Z", "cloud_cover": 12.0, "assets": {}},
            ],
            "rationale": ["incident lifecycle"],
            "explainability": {
                "coverage": 0.68,
                "consensus": 0.64,
                "signals": [
                    {
                        "key": "sentinel_change",
                        "source": "sentinel-2",
                        "hazard_type": "surface-change",
                        "status": "ok",
                        "score": score,
                        "weight": 0.35,
                        "contribution": round(score * 0.35, 4),
                        "reliability": 1.0,
                        "details": "Synthetic signal.",
                    }
                ],
            },
        }

    monkeypatch.setattr(webapp, "run_pipeline", stub_pipeline)
    client = webapp.app.test_client()

    analysis_response = client.post("/api/analyze", json={"lat": 35.0, "lon": -120.0, "mode": "sample"})
    assert analysis_response.status_code == 200
    first_history_id = analysis_response.get_json()["history_id"]

    create_response = client.post("/api/incidents", json={"history_id": first_history_id})
    assert create_response.status_code == 201
    create_payload = create_response.get_json()
    assert create_payload["ok"] is True
    assert create_payload["incident"]["status"] == "open"
    incident_id = create_payload["incident"]["id"]

    list_response = client.get("/api/incidents")
    assert list_response.status_code == 200
    listed = list_response.get_json()["items"]
    assert len(listed) == 1
    assert listed[0]["id"] == incident_id

    rescan_response = client.post(f"/api/incidents/{incident_id}/rescan", json={})
    assert rescan_response.status_code == 200
    rescan_payload = rescan_response.get_json()
    assert rescan_payload["ok"] is True
    assert rescan_payload["analysis"]["history_id"] != first_history_id
    assert rescan_payload["incident"]["latest_history_id"] == rescan_payload["analysis"]["history_id"]
    assert rescan_payload["incident"]["latest_threat_level"] == "high"

    close_response = client.post(f"/api/incidents/{incident_id}/close", json={})
    assert close_response.status_code == 200
    close_payload = close_response.get_json()
    assert close_payload["ok"] is True
    assert close_payload["incident"]["status"] == "closed"
