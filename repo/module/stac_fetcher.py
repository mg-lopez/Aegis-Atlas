"""Utilities for discovering and downloading Sentinel-2 scenes from STAC.

This module queries the Microsoft Planetary Computer STAC API for
Sentinel-2 L2A scenes and provides a helper to download a useful raster asset.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import planetary_computer
import pystac_client
import requests

PLANETARY_COMPUTER_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
SENTINEL_COLLECTION = "sentinel-2-l2a"


def find_best_sentinel_scenes(
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    max_cloud: int = 30,
) -> list[dict[str, Any]]:
    """Find recent Sentinel-2 scenes in an area with low cloud cover.

    Args:
        bbox: Bounding box in ``(min_lon, min_lat, max_lon, max_lat)`` order.
        start_date: Start date in ISO-like ``YYYY-MM-DD`` format.
        end_date: End date in ISO-like ``YYYY-MM-DD`` format.
        max_cloud: Maximum allowed cloud cover percentage.

    Returns:
        Up to five scene metadata dictionaries with keys ``id``, ``datetime``,
        ``assets`` (href-only mapping), ``geometry``, and ``properties``.

    Raises:
        ValueError: If input parameters are invalid.
        RuntimeError: If the STAC query fails unexpectedly.
    """
    if len(bbox) != 4:
        raise ValueError("bbox must be a 4-tuple: (min_lon, min_lat, max_lon, max_lat)")

    min_lon, min_lat, max_lon, max_lat = bbox
    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValueError("bbox coordinates are invalid: min values must be less than max values")

    try:
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
    except ValueError as exc:
        raise ValueError("start_date and end_date must be valid ISO date strings") from exc

    if max_cloud < 0 or max_cloud > 100:
        raise ValueError("max_cloud must be between 0 and 100")

    dt_range = f"{start_date}/{end_date}"

    try:
        client = pystac_client.Client.open(PLANETARY_COMPUTER_STAC_URL)
        search = client.search(
            collections=[SENTINEL_COLLECTION],
            bbox=list(bbox),
            datetime=dt_range,
            query={"eo:cloud_cover": {"lt": max_cloud}},
        )
        items = list(search.items())
    except Exception as exc:  # pragma: no cover - network/service errors
        raise RuntimeError(f"Failed to query STAC API: {exc}") from exc

    def _item_dt(item: Any) -> datetime:
        value = item.properties.get("datetime")
        if not value:
            return datetime.min
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min

    items.sort(key=_item_dt, reverse=True)

    results: list[dict[str, Any]] = []
    for item in items[:5]:
        results.append(
            {
                "id": item.id,
                "datetime": item.properties.get("datetime"),
                "assets": {name: asset.href for name, asset in item.assets.items()},
                "geometry": item.geometry,
                "properties": item.properties,
            }
        )

    return results


def download_scene(scene: dict[str, Any], out_dir: str | Path) -> Path:
    """Download a raster asset for a Sentinel-2 scene to a local directory.

    Asset selection priority is:
    1) ``visual`` if available,
    2) otherwise ``B04``, then ``B03``, then ``B02``.

    Args:
        scene: Scene metadata dictionary (as returned by
            :func:`find_best_sentinel_scenes`) containing ``id`` and ``assets``.
        out_dir: Output directory where the downloaded file should be saved.

    Returns:
        Path to the downloaded file.

    Raises:
        ValueError: If scene metadata is missing required fields.
        RuntimeError: If no suitable asset exists or download fails.
    """
    scene_id = scene.get("id")
    assets = scene.get("assets")

    if not scene_id or not isinstance(assets, dict):
        raise ValueError("scene must include 'id' and an 'assets' dictionary")

    asset_key = next((key for key in ("visual", "B04", "B03", "B02") if key in assets), None)
    if asset_key is None:
        raise RuntimeError("No downloadable asset found. Expected one of: visual, B04, B03, B02")

    href = assets[asset_key]
    if not isinstance(href, str) or not href:
        raise ValueError(f"Invalid href for asset '{asset_key}'")

    signed_href = planetary_computer.sign(href)

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    suffix = Path(href).suffix or ".tif"
    filename = f"{scene_id}_{asset_key}{suffix}"
    destination = out_path / filename

    try:
        with requests.get(signed_href, stream=True, timeout=120) as response:
            response.raise_for_status()
            with destination.open("wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
    except Exception as exc:  # pragma: no cover - network/service errors
        raise RuntimeError(f"Failed to download scene asset: {exc}") from exc

    return destination
