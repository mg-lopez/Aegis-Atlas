"""Simple remote-sensing analysis helpers for the prototype pipeline."""

from __future__ import annotations

import numpy as np


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


def detect_change_from_band_difference(
    before_band: np.ndarray,
    after_band: np.ndarray,
    change_threshold: float = 0.15,
) -> dict[str, float | bool]:
    """Compute a normalized mean absolute band difference change score.

    Args:
        before_band: Prior observation raster values.
        after_band: Recent observation raster values, same shape as ``before_band``.
        change_threshold: Alert threshold in normalized units.

    Returns:
        Dict with score and whether the threshold is exceeded.
    """

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
