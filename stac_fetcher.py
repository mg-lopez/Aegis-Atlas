"""Helpers for finding Sentinel-2 scenes from Microsoft Planetary Computer STAC."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit
import os

import requests

try:
    import planetary_computer
except ModuleNotFoundError:  # pragma: no cover - optional at test time
    planetary_computer = None

try:
    from pystac_client import Client
except ModuleNotFoundError:  # pragma: no cover - optional at test time
    Client = None
try:
    from pystac_client.stac_api_io import StacApiIO
except ModuleNotFoundError:  # pragma: no cover - optional at test time
    StacApiIO = None

PLANETARY_COMPUTER_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
DEFAULT_COLLECTION = "sentinel-2-l2a"
STAC_HTTP_TIMEOUT = float(os.getenv("AEGIS_STAC_HTTP_TIMEOUT_SECONDS", "12"))
STAC_MAX_RETRIES = int(os.getenv("AEGIS_STAC_MAX_RETRIES", "1"))


@dataclass(frozen=True)
class SceneSummary:
    """A minimal, serializable summary of a selected STAC item."""

    id: str
    datetime: str
    cloud_cover: float | None
    assets: dict[str, str]



def scene_to_dict(scene: SceneSummary) -> dict[str, Any]:
    """Return a JSON-serializable scene dictionary."""

    return asdict(scene)


def _get_cloud_cover(item: Any) -> float:
    """Return cloud-cover value for ranking when available."""

    cloud = item.properties.get("eo:cloud_cover")
    if cloud is None:
        return 100.0
    return float(cloud)


def _to_scene_summary(item: Any) -> SceneSummary:
    """Convert a STAC item to a compact :class:`SceneSummary`."""

    dt = item.properties.get("datetime") or ""
    cloud = item.properties.get("eo:cloud_cover")
    assets = {name: asset.href for name, asset in item.assets.items()}
    return SceneSummary(
        id=item.id,
        datetime=dt,
        cloud_cover=float(cloud) if cloud is not None else None,
        assets=assets,
    )


def find_best_sentinel_scenes(
    bbox: Iterable[float],
    start_date: str,
    end_date: str,
    max_cloud: float = 20.0,
    limit: int = 3,
    collection: str = DEFAULT_COLLECTION,
) -> list[SceneSummary]:
    """Find the best Sentinel-2 L2A scenes for a region and date range."""

    time_range = f"{start_date}/{end_date}"
    if Client is None:
        raise ModuleNotFoundError("pystac-client is required to query STAC")

    modifier = planetary_computer.sign_inplace if planetary_computer is not None else None
    if StacApiIO is not None:
        stac_io = StacApiIO(timeout=STAC_HTTP_TIMEOUT, max_retries=STAC_MAX_RETRIES)
        client = Client.open(
            PLANETARY_COMPUTER_STAC_URL,
            modifier=modifier,
            stac_io=stac_io,
            timeout=STAC_HTTP_TIMEOUT,
        )
    else:
        client = Client.open(PLANETARY_COMPUTER_STAC_URL, modifier=modifier, timeout=STAC_HTTP_TIMEOUT)

    search = client.search(
        collections=[collection],
        bbox=list(bbox),
        datetime=time_range,
        query={"eo:cloud_cover": {"lte": max_cloud}},
        limit=max(limit, 1),
    )

    items = list(search.items())
    filtered = [item for item in items if _get_cloud_cover(item) <= float(max_cloud)]
    ranked = sorted(filtered, key=_get_cloud_cover)
    return [_to_scene_summary(item) for item in ranked[:limit]]


def download_asset(
    scene: SceneSummary,
    asset_name: str,
    download_dir: str | Path,
    debug_dir: str | Path,
) -> Path:
    """Download one scene asset and append signed URL diagnostics to debug logs."""

    if asset_name not in scene.assets:
        raise KeyError(f"Asset '{asset_name}' not available in scene {scene.id}")

    raw_href = scene.assets[asset_name]
    signed_href = (
        planetary_computer.sign(raw_href)
        if planetary_computer is not None and raw_href.startswith("http")
        else raw_href
    )

    debug_path = Path(debug_dir)
    debug_path.mkdir(parents=True, exist_ok=True)
    log_file = debug_path / "signed_urls.jsonl"
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {
                    "scene_id": scene.id,
                    "asset": asset_name,
                    "raw_href": raw_href,
                    "signed_href": signed_href,
                }
            )
            + "\n"
        )

    out_dir = Path(download_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = _asset_suffix(raw_href)
    destination = out_dir / f"{scene.id}_{asset_name}{suffix}"

    if raw_href.startswith("http"):
        with requests.get(signed_href, stream=True, timeout=(10, 45)) as response:
            response.raise_for_status()
            with destination.open("wb") as out:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        out.write(chunk)
    else:
        source = Path(raw_href)
        destination.write_bytes(source.read_bytes())

    return destination


def _asset_suffix(href: str) -> str:
    """Return a safe extension for local asset filenames."""

    parsed = urlsplit(href)
    source_path = parsed.path if parsed.scheme else href
    suffix = Path(unquote(source_path)).suffix
    if not suffix:
        return ".tif"
    if len(suffix) > 10 or any(char in suffix for char in ("?", "&", "=")):
        return ".tif"
    return suffix
