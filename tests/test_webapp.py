"""Tests for hackathon dashboard API."""

from __future__ import annotations

import webapp
import watchlists


def test_analyze_endpoint_returns_expected_payload_shape(monkeypatch):
    monkeypatch.setattr(
        webapp,
        "run_pipeline",
        lambda **kwargs: {
            "threat_level": "medium",
            "score": 0.44,
            "confidence": "medium",
            "confidence_score": 0.62,
            "recommended_action": "Prepare to evacuate.",
            "sources": ["scene-a", "scene-b"],
            "source_details": [
                {"id": "scene-a", "datetime": "2026-03-06T12:00:00Z", "cloud_cover": 7.0, "assets": {}},
                {"id": "scene-b", "datetime": "2026-03-05T12:00:00Z", "cloud_cover": 11.0, "assets": {}},
            ],
            "rationale": [
                "sentinel_change: score 0.44 with weight 0.55 (Spectral and structural scene-delta analysis.)",
                "gdacs: no numeric score (No active GDACS event intersecting selected AOI.)",
            ],
            "explainability": {
                "active_signal_count": 1,
                "coverage": 0.55,
                "consensus": 0.75,
                "signals": [
                    {
                        "key": "sentinel_change",
                        "source": "sentinel-2",
                        "hazard_type": "surface-change",
                        "status": "ok",
                        "score": 0.44,
                        "weight": 0.55,
                        "contribution": 0.242,
                        "details": "Spectral and structural scene-delta analysis.",
                    }
                ],
            },
        },
    )

    client = webapp.app.test_client()
    response = client.post("/api/analyze", json={"lat": 40.7, "lon": -74.0, "mode": "sample"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["mode"] == "sample"
    assert payload["threat_level"] == "medium"
    assert payload["confidence"] == "medium"
    assert payload["confidence_score"] == 0.62
    assert payload["query"]["lat"] == 40.7
    assert payload["query"]["lon"] == -74.0
    assert len(payload["query"]["bbox"]) == 4
    assert payload["query"]["radius_km"] == 25.0
    assert payload["query"]["lens"] == "general"
    assert payload["query"]["analysis_key"]
    assert isinstance(payload["rationale"], list)
    assert payload["rationale"][0].startswith("sentinel_change:")
    assert "signals" in payload["explainability"]
    assert payload["explainability"]["signals"][0]["key"] == "sentinel_change"
    assert payload["brief"]["headline"]
    assert payload["brief"]["analysis_mode_label"] == "Sample demo"
    assert payload["brief"]["quality_band"] in {"limited", "moderate", "strong"}
    assert payload["brief"]["lens_label"] == "General"
    assert payload["evidence_health"]["overall_label"] == "demo"
    assert payload["evidence_health"]["satellite"]["label"] == "demo"
    assert "external_feeds" in payload["evidence_health"]
    assert "trend" in payload
    assert payload["lens_insight"]["headline"]
    assert payload["lens_insight"]["bullets"]
    assert payload["lens_insight"]["actions"]
    assert payload["lens_insight"]["confidence_note"]
    assert payload["lens_insight"]["caveat_tone"] in {"watch", "critical", "healthy", "neutral"}
    assert payload["lens_insight"]["action_priority"] in {"escalate", "act", "review", "monitor", "watch"}
    assert "incident_context" in payload


def test_analyze_endpoint_rejects_missing_coordinates():
    client = webapp.app.test_client()
    response = client.post("/api/analyze", json={"lat": 12.0})

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["ok"] is False
    assert "Missing required field" in payload["error"]


def test_analyze_endpoint_returns_504_on_pipeline_timeout(monkeypatch):
    monkeypatch.setattr(
        webapp,
        "_run_pipeline_with_timeout",
        lambda **kwargs: (_ for _ in ()).throw(TimeoutError("Analysis timed out after 75s in live mode.")),
    )

    client = webapp.app.test_client()
    response = client.post("/api/analyze", json={"lat": 40.7, "lon": -74.0, "mode": "live"})

    assert response.status_code == 504
    payload = response.get_json()
    assert payload["ok"] is False
    assert "timed out" in payload["error"]


def test_presets_endpoint_returns_seed_hotspots():
    client = webapp.app.test_client()
    response = client.get("/api/presets")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["featured_id"]
    assert payload["items"]
    assert payload["items"][0]["id"]
    assert "radius_km" in payload["items"][0]
    assert "lens" in payload["items"][0]
    assert "demo_headline" in payload["items"][0]
    assert "watchlist_seed" in payload["items"][0]


def test_lenses_endpoint_lists_available_customer_views():
    client = webapp.app.test_client()
    response = client.get("/api/lenses")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert any(item["id"] == "security" for item in payload["items"])


def test_customer_lens_reweights_score_and_brief(monkeypatch):
    monkeypatch.setattr(
        webapp,
        "run_pipeline",
        lambda **kwargs: {
            "threat_level": "medium",
            "score": 0.35,
            "confidence": "medium",
            "confidence_score": 0.61,
            "recommended_action": "Prepare to evacuate.",
            "sources": ["scene-a"],
            "rationale": ["base rationale"],
            "explainability": {
                "active_signal_count": 4,
                "coverage": 0.8,
                "consensus": 0.72,
                "signals": [
                    {
                        "key": "sentinel_change",
                        "source": "sentinel-2",
                        "hazard_type": "surface-change",
                        "status": "ok",
                        "score": 0.2,
                        "weight": 0.35,
                        "reliability": 1.0,
                        "effective_weight": 0.35,
                        "contribution": 0.07,
                        "details": "Satellite change.",
                    },
                    {
                        "key": "gdacs",
                        "source": "gdacs",
                        "hazard_type": "global-alert",
                        "status": "ok",
                        "score": 0.2,
                        "weight": 0.15,
                        "reliability": 1.0,
                        "effective_weight": 0.15,
                        "contribution": 0.03,
                        "details": "Alert feed.",
                    },
                    {
                        "key": "usgs_seismic",
                        "source": "usgs",
                        "hazard_type": "earthquake",
                        "status": "ok",
                        "score": 0.1,
                        "weight": 0.10,
                        "reliability": 1.0,
                        "effective_weight": 0.10,
                        "contribution": 0.01,
                        "details": "Seismic feed.",
                    },
                    {
                        "key": "geo_conflict",
                        "source": "regional-risk",
                        "hazard_type": "geopolitical-composite",
                        "status": "ok",
                        "score": 0.6,
                        "weight": 0.40,
                        "reliability": 1.0,
                        "effective_weight": 0.40,
                        "contribution": 0.24,
                        "details": "Conflict context.",
                    },
                ],
            },
        },
    )

    client = webapp.app.test_client()
    logistics = client.post("/api/analyze", json={"lat": 31.5, "lon": 34.8, "mode": "sample", "lens": "logistics"})
    security = client.post("/api/analyze", json={"lat": 31.5, "lon": 34.8, "mode": "sample", "lens": "security"})

    logistics_payload = logistics.get_json()
    security_payload = security.get_json()
    assert logistics_payload["lens"] == "logistics"
    assert security_payload["lens"] == "security"
    assert security_payload["score"] > logistics_payload["score"]
    assert security_payload["brief"]["lens_label"] == "Security / Defense"
    assert any("security" in tag.lower() for tag in security_payload["brief"]["customer_tags"])
    assert "route" in logistics_payload["lens_insight"]["headline"].lower() or "corridor" in logistics_payload["lens_insight"]["headline"].lower()
    assert "security" in security_payload["lens_insight"]["headline"].lower() or "protective" in security_payload["lens_insight"]["headline"].lower()


def test_evidence_health_flags_live_fast_as_degraded_when_inputs_are_stale(monkeypatch):
    monkeypatch.setattr(
        webapp,
        "run_pipeline",
        lambda **kwargs: {
            "threat_level": "medium",
            "score": 0.33,
            "confidence": "medium",
            "confidence_score": 0.28,
            "recommended_action": "Monitor closely.",
            "sources": ["scene-old"],
            "source_details": [
                {"id": "scene-old", "datetime": "2024-01-01T00:00:00Z", "cloud_cover": 22.0, "assets": {}},
            ],
            "rationale": ["stale-evidence test"],
            "explainability": {
                "active_signal_count": 2,
                "coverage": 0.31,
                "consensus": 0.38,
                "signals": [
                    {
                        "key": "sentinel_change",
                        "source": "sentinel-2-stac-meta",
                        "hazard_type": "surface-change",
                        "status": "ok",
                        "score": 0.2,
                        "weight": 0.35,
                        "reliability": 1.0,
                        "effective_weight": 0.35,
                        "contribution": 0.07,
                        "details": "Fast-mode estimate from STAC metadata.",
                    },
                    {
                        "key": "gdacs",
                        "source": "gdacs",
                        "hazard_type": "global-alert",
                        "status": "unavailable",
                        "score": 0.18,
                        "weight": 0.15,
                        "reliability": 0.2,
                        "effective_weight": 0.03,
                        "contribution": 0.027,
                        "details": "GDACS feed unavailable.",
                    },
                    {
                        "key": "geo_conflict",
                        "source": "regional-risk-model+travel-advisory+gdelt",
                        "hazard_type": "geopolitical-composite",
                        "status": "insufficient_data",
                        "score": 0.24,
                        "weight": 0.4,
                        "reliability": 0.25,
                        "effective_weight": 0.1,
                        "contribution": 0.096,
                        "details": "Travel/headline cache stale.",
                    },
                ],
            },
        },
    )

    client = webapp.app.test_client()
    response = client.post("/api/analyze", json={"lat": 35.0, "lon": -120.0, "mode": "live"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["evidence_health"]["overall_label"] in {"watch", "degraded"}
    assert payload["evidence_health"]["satellite"]["label"] == "stale"
    assert payload["evidence_health"]["external_feeds"]["label"] == "partial"
    assert any("Fast mode" in note or "Fast scout" in note for note in payload["evidence_health"]["notes"])


def test_watchlist_alert_preferences_scan_and_delete(monkeypatch, tmp_path):
    monkeypatch.setattr(watchlists, "WATCHLISTS_FILE", tmp_path / "watchlists.json")
    monkeypatch.setattr(
        webapp,
        "_run_pipeline_with_timeout",
        lambda **kwargs: {
            "threat_level": "high",
            "score": 0.78,
            "confidence": "high",
            "confidence_score": 0.84,
            "recommended_action": "Move to protective posture.",
            "sources": ["scene-a"],
            "source_details": [],
            "rationale": ["elevated watchlist test"],
            "explainability": {
                "active_signal_count": 2,
                "coverage": 0.7,
                "consensus": 0.68,
                "signals": [
                    {
                        "key": "headline_conflict",
                        "source": "gdelt",
                        "hazard_type": "geopolitical-composite",
                        "status": "ok",
                        "score": 0.78,
                        "weight": 0.35,
                        "reliability": 0.9,
                        "effective_weight": 0.315,
                        "contribution": 0.246,
                        "details": "San Francisco: Escalation bulletin.",
                    }
                ],
            },
        },
    )

    client = webapp.app.test_client()
    created = client.post(
        "/api/watchlists",
        json={
            "name": "Priority Assets",
            "members": [{"label": "HQ", "lat": 37.7749, "lon": -122.4194}],
        },
    )
    assert created.status_code == 201
    watchlist_id = created.get_json()["watchlist"]["id"]

    updated = client.put(
        f"/api/watchlists/{watchlist_id}/alerts",
        json={
            "email_to": "ops@example.com",
            "sms_to": "+15551234567",
            "email_enabled": True,
            "sms_enabled": True,
            "threshold": "high",
        },
    )
    assert updated.status_code == 200
    updated_payload = updated.get_json()
    assert updated_payload["watchlist"]["alerts"]["email_to"] == "ops@example.com"
    assert updated_payload["watchlist"]["alerts"]["sms_to"] == "+15551234567"

    scanned = client.post(
        f"/api/watchlists/{watchlist_id}/scan",
        json={"mode": "sample", "lens": "general", "radius_km": 25},
    )
    assert scanned.status_code == 200
    scan_payload = scanned.get_json()
    notifications = scan_payload["results"][0]["notifications"]
    assert any(item["channel"] == "email" for item in notifications)
    assert any(item["channel"] == "sms" for item in notifications)

    deleted = client.delete(f"/api/watchlists/{watchlist_id}")
    assert deleted.status_code == 200
    listed = client.get("/api/watchlists")
    assert listed.status_code == 200
    assert listed.get_json()["items"] == []
