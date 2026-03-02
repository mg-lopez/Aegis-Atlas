"""Unit tests for STAC fetcher scene ranking and filtering behavior."""

from __future__ import annotations

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
    return SimpleNamespace(id=item_id, properties=properties, assets={"B04": object(), "B08": object()})


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

    assert [scene.id for scene in scenes] == ["known", "unknown"]
