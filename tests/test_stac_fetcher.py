"""Unit tests for STAC fetcher scene ranking and filtering behavior."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import stac_fetcher


class FakeSearch:
    def __init__(self, items):
        self._items = items

    def items(self):
        return iter(self._items)


class FakeClient:
    def __init__(self, items):
        self._items = items
        self.search_calls = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return FakeSearch(self._items)


class FakeClientModule:
    @staticmethod
    def open(*args, **kwargs):
        return FakeClientModule._client


def make_item(item_id: str, cloud: float | None):
    properties = {"datetime": "2024-08-01T00:00:00Z"}
    if cloud is not None:
        properties["eo:cloud_cover"] = cloud
    return SimpleNamespace(id=item_id, properties=properties, assets={"B04": SimpleNamespace(href="https://example/B04.tif"), "B08": SimpleNamespace(href="https://example/B08.tif")})


def test_find_best_sentinel_scenes_sorts_by_cloud_cover(monkeypatch):
    items = [make_item("high", 40), make_item("low", 5), make_item("mid", 20)]
    FakeClientModule._client = FakeClient(items)

    monkeypatch.setattr(stac_fetcher, "Client", FakeClientModule)

    scenes = stac_fetcher.find_best_sentinel_scenes(
        bbox=[0, 0, 1, 1],
        start_date="2024-08-01",
        end_date="2024-08-31",
        max_cloud=50,
        limit=2,
    )

    assert [scene.id for scene in scenes] == ["low", "mid"]


def test_find_best_sentinel_scenes_filters_cloud_cover_when_response_exceeds_threshold(monkeypatch):
    items = [make_item("clear", 3), make_item("cloudy", 70), make_item("acceptable", 20)]
    client = FakeClient(items)
    FakeClientModule._client = client
    monkeypatch.setattr(stac_fetcher, "Client", FakeClientModule)

    scenes = stac_fetcher.find_best_sentinel_scenes(
        bbox=[-1, -1, 1, 1],
        start_date="2024-07-01",
        end_date="2024-07-31",
        max_cloud=25,
        limit=3,
    )

    assert [scene.id for scene in scenes] == ["clear", "acceptable"]
    assert client.search_calls[0]["query"] == {"eo:cloud_cover": {"lte": 25}}


def test_find_best_sentinel_scenes_handles_missing_cloud_metadata(monkeypatch):
    items = [make_item("unknown", None), make_item("known", 15)]
    FakeClientModule._client = FakeClient(items)
    monkeypatch.setattr(stac_fetcher, "Client", FakeClientModule)

    scenes = stac_fetcher.find_best_sentinel_scenes(
        bbox=[-1, -1, 1, 1],
        start_date="2024-07-01",
        end_date="2024-07-31",
        max_cloud=80,
        limit=2,
    )

    assert [scene.id for scene in scenes] == ["known"]


def test_download_asset_uses_safe_suffix_for_signed_urls(tmp_path, monkeypatch):
    scene = stac_fetcher.SceneSummary(
        id="scene-1",
        datetime="2024-08-01T00:00:00Z",
        cloud_cover=2.0,
        assets={
            "B04": (
                "https://example.com/path/B04.tif"
                "?st=2026-03-06T00%3A08%3A25Z&se=2026-03-07T00%3A53%3A25Z"
                "&sig=abcdef"
            )
        },
    )

    class FakeResponse:
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=1024):  # noqa: ARG002
            yield b"fake-bytes"

    monkeypatch.setattr(stac_fetcher.requests, "get", lambda *args, **kwargs: FakeResponse())

    out = stac_fetcher.download_asset(scene, "B04", tmp_path / "assets", tmp_path / "debug")
    assert out.exists()
    assert out.suffix == ".tif"
    assert "?" not in out.name
    assert out.name == "scene-1_B04.tif"
