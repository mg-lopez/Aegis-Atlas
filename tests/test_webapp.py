"""Tests for hackathon dashboard API."""

from __future__ import annotations

import webapp


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
    assert isinstance(payload["rationale"], list)
    assert payload["rationale"][0].startswith("sentinel_change:")
    assert "signals" in payload["explainability"]
    assert payload["explainability"]["signals"][0]["key"] == "sentinel_change"


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
