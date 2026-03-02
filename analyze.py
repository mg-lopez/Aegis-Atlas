"""Simple Sentinel-2 analysis utilities.

Usage
-----
>>> rgb, cloud = cloud_mask_and_rgb("/path/to/S2_scene")
>>> score = change_score(rgb_baseline, rgb_recent, cloud_baseline, cloud_recent)

Key behavior and edge cases
---------------------------
* ``cloud_mask_and_rgb`` expects Sentinel-2 bands B04, B03, and B02 to exist under
  ``scene_path`` (or in the parent directory when a file path is provided).
* Cloud masking priority is:
  1. use SCL cloud-like classes when an SCL raster exists,
  2. otherwise use a naive B8A threshold,
  3. otherwise return an all-clear (all ``False``) mask.
* ``change_score`` computes a robust median-brightness change over non-cloud pixels.
  If all pixels are masked, it returns ``0.0``.
* All shape mismatches raise ``ValueError`` with explicit diagnostics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

_VALID_EXTENSIONS = (".jp2", ".tif", ".tiff")


def _scene_root(scene_path: str) -> Path:
    """Return directory to search for Sentinel-2 bands."""
    root = Path(scene_path)
    return root if root.is_dir() else root.parent


def _find_band_file(scene_dir: Path, band_token: str) -> Optional[Path]:
    """Find a Sentinel-2 band file containing the given token."""
    candidates = [
        p
        for p in scene_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in _VALID_EXTENSIONS and band_token in p.stem
    ]
    if not candidates:
        return None

    candidates.sort(key=lambda p: (len(p.parts), str(p)))
    return candidates[0]


def _read_single_band(path: Path) -> np.ndarray:
    """Read first raster band as float32."""
    import rasterio

    with rasterio.open(path) as src:
        arr = src.read(1)
    return arr.astype(np.float32, copy=False)


def compute_simple_cloud_mask(scl_band: np.ndarray) -> np.ndarray:
    """Create a boolean cloud mask from Sentinel-2 scene classification layer.

    Cloud-like classes follow Sentinel-2 SCL conventions:
      - 8: cloud medium probability
      - 9: cloud high probability
      - 10: thin cirrus
      - 11: snow/ice
    """
    cloud_classes = np.array([8, 9, 10, 11])
    return np.isin(scl_band, cloud_classes)


def cloud_mask_and_rgb(scene_path: str) -> tuple[np.ndarray, np.ndarray]:
    """Load Sentinel-2 RGB and compute a cloud mask.

    Parameters
    ----------
    scene_path:
        Path to a Sentinel-2 scene directory (or a file inside the scene).

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``(rgb_array, cloud_mask)`` where ``rgb_array`` has shape ``(H, W, 3)`` and
        ``cloud_mask`` has shape ``(H, W)``.

    Notes
    -----
    * SCL classes 3, 8, 9, 10, 11 are treated as cloud/obstruction classes.
    * The B8A fallback uses a naive threshold (``> 0.25`` for reflectance-like values,
      or ``> 2500`` for scaled integer-like values).
    """
    scene_dir = _scene_root(scene_path)

    b04_path = _find_band_file(scene_dir, "B04")
    b03_path = _find_band_file(scene_dir, "B03")
    b02_path = _find_band_file(scene_dir, "B02")

    missing = [
        token
        for token, path in (("B04", b04_path), ("B03", b03_path), ("B02", b02_path))
        if path is None
    ]
    if missing:
        raise FileNotFoundError(f"Missing required Sentinel-2 bands: {', '.join(missing)}")

    red = _read_single_band(b04_path)
    green = _read_single_band(b03_path)
    blue = _read_single_band(b02_path)

    if not (red.shape == green.shape == blue.shape):
        raise ValueError(
            "RGB bands must share the same shape; got "
            f"B04={red.shape}, B03={green.shape}, B02={blue.shape}"
        )

    rgb_array = np.dstack((red, green, blue))

    scl_path = _find_band_file(scene_dir, "SCL")
    if scl_path is not None:
        scl = _read_single_band(scl_path)
        if scl.shape != red.shape:
            raise ValueError(f"SCL shape {scl.shape} does not match RGB shape {red.shape}.")
        cloud_mask = np.isin(scl.astype(np.int16), [3, 8, 9, 10, 11])
    else:
        b8a_path = _find_band_file(scene_dir, "B8A")
        if b8a_path is not None:
            b8a = _read_single_band(b8a_path)
            if b8a.shape != red.shape:
                raise ValueError(f"B8A shape {b8a.shape} does not match RGB shape {red.shape}.")
            thr = 2500.0 if np.nanmax(b8a) > 2.0 else 0.25
            cloud_mask = b8a > thr
        else:
            cloud_mask = np.zeros(red.shape, dtype=bool)

    return rgb_array, cloud_mask.astype(bool, copy=False)


def change_score(
    baseline_rgb: np.ndarray,
    recent_rgb: np.ndarray,
    cloud_mask_baseline: Optional[np.ndarray] = None,
    cloud_mask_recent: Optional[np.ndarray] = None,
) -> float:
    """Compute a normalized brightness change score in ``[0, 1]``.

    The score is:

    ``abs(median(recent) - median(baseline)) / (abs(median(recent)) + abs(median(baseline)) + eps)``

    where medians are computed from per-pixel RGB mean brightness over pixels that are
    not marked cloudy in either input cloud mask.

    Edge cases
    ----------
    * Returns ``0.0`` if there are no valid non-cloud pixels.
    * Raises ``ValueError`` for image/mask shape mismatches.
    """
    baseline = np.asarray(baseline_rgb, dtype=np.float32)
    recent = np.asarray(recent_rgb, dtype=np.float32)

    if baseline.shape != recent.shape:
        raise ValueError(
            f"baseline_rgb and recent_rgb must share shape; got {baseline.shape} and {recent.shape}"
        )
    if baseline.ndim != 3 or baseline.shape[-1] != 3:
        raise ValueError(f"Expected RGB arrays of shape (H, W, 3); got {baseline.shape}.")

    valid = np.ones(baseline.shape[:2], dtype=bool)
    if cloud_mask_baseline is not None:
        cm_b = np.asarray(cloud_mask_baseline, dtype=bool)
        if cm_b.shape != valid.shape:
            raise ValueError(
                f"cloud_mask_baseline shape {cm_b.shape} does not match image shape {valid.shape}."
            )
        valid &= ~cm_b
    if cloud_mask_recent is not None:
        cm_r = np.asarray(cloud_mask_recent, dtype=bool)
        if cm_r.shape != valid.shape:
            raise ValueError(
                f"cloud_mask_recent shape {cm_r.shape} does not match image shape {valid.shape}."
            )
        valid &= ~cm_r

    if not np.any(valid):
        return 0.0

    baseline_brightness = baseline.mean(axis=2)
    recent_brightness = recent.mean(axis=2)

    b_med = float(np.median(baseline_brightness[valid]))
    r_med = float(np.median(recent_brightness[valid]))

    eps = 1e-6
    score = abs(r_med - b_med) / (abs(r_med) + abs(b_med) + eps)
    return float(np.clip(score, 0.0, 1.0))


def detect_change_from_band_difference(
    before_band: np.ndarray,
    after_band: np.ndarray,
    change_threshold: float = 0.15,
) -> dict[str, float | bool]:
    """Compute a normalized mean absolute band difference change score."""
    if before_band.shape != after_band.shape:
        raise ValueError("before_band and after_band must have the same shape")

    before = before_band.astype(np.float32)
    after = after_band.astype(np.float32)

    denom = np.maximum(np.abs(before) + np.abs(after), 1e-6)
    normalized_diff = np.abs(after - before) / denom
    score = float(np.mean(normalized_diff))
    return {
        "change_score": score,
        "alert": score >= change_threshold,
        "threshold": float(change_threshold),
    }
