"""Helpers for finding Sentinel-2 scenes from Microsoft Planetary Computer STAC."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

try:
    import planetary_computer
except ModuleNotFoundError:  # pragma: no cover - optional at test time
    planetary_computer = None

try:
    from pystac_client import Client
except ModuleNotFoundError:  # pragma: no cover - optional at test time
    Client = None

PLANETARY_COMPUTER_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
DEFAULT_COLLECTION = "sentinel-2-l2a"


@dataclass(frozen=True)
class SceneSummary:
    """A minimal, serializable summary of a selected STAC item."""

    id: str
    datetime: str
    cloud_cover: float | None
    assets: list[str]


def _get_cloud_cover(item: Any) -> float:
    """Return cloud-cover value for ranking when available.

    Items with no cloud metadata are ranked last by returning 100.
    """

    cloud = item.properties.get("eo:cloud_cover")
    if cloud is None:
        return 100.0
    return float(cloud)


def _to_scene_summary(item: Any) -> SceneSummary:
    """Convert a STAC item to a compact :class:`SceneSummary`."""

    dt = item.properties.get("datetime") or ""
    cloud = item.properties.get("eo:cloud_cover")
    return SceneSummary(
        id=item.id,
        datetime=dt,
        cloud_cover=float(cloud) if cloud is not None else None,
        assets=sorted(item.assets.keys()),
    )


def find_best_sentinel_scenes(
    bbox: Iterable[float],
    start_date: str,
    end_date: str,
    max_cloud: float = 20.0,
    limit: int = 3,
    collection: str = DEFAULT_COLLECTION,
) -> list[SceneSummary]:
    """Find the best Sentinel-2 L2A scenes for a region and date range.

    Args:
        bbox: Bounding box as ``[min_lon, min_lat, max_lon, max_lat]``.
        start_date: Start date (inclusive) in ``YYYY-MM-DD`` format.
        end_date: End date (inclusive) in ``YYYY-MM-DD`` format.
        max_cloud: Maximum acceptable cloud cover percentage.
        limit: Maximum number of scenes to return.
        collection: STAC collection id, defaults to Sentinel-2 L2A.

    Returns:
        A list of scenes sorted from lowest cloud-cover to highest.
    """

    time_range = f"{start_date}/{end_date}"
    if Client is None:
        raise ModuleNotFoundError("pystac-client is required to query STAC")

    modifier = planetary_computer.sign_inplace if planetary_computer is not None else None
    client = Client.open(PLANETARY_COMPUTER_STAC_URL, modifier=modifier)

    search = client.search(
        collections=[collection],
        bbox=list(bbox),
        datetime=time_range,
        query={"eo:cloud_cover": {"lte": max_cloud}},
        limit=max(limit, 10),
    )

    items = list(search.items())
    filtered = [item for item in items if _get_cloud_cover(item) <= float(max_cloud)]
    ranked = sorted(filtered, key=_get_cloud_cover)
    return [_to_scene_summary(item) for item in ranked[:limit]]
