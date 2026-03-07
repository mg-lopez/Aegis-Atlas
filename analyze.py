"""Sentinel-2 change analysis utilities with debug artifact generation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import numpy as np
try:
    from skimage import exposure
    from skimage.io import imsave
    from skimage.metrics import structural_similarity
except ModuleNotFoundError:  # pragma: no cover
    class _Exposure:
        @staticmethod
        def rescale_intensity(arr: np.ndarray, out_range: tuple[int, int] = (0, 255)) -> np.ndarray:
            mn, mx = float(np.min(arr)), float(np.max(arr))
            if mx - mn < 1e-6:
                return np.zeros_like(arr)
            lo, hi = out_range
            return (arr - mn) / (mx - mn) * (hi - lo) + lo

    exposure = _Exposure()

    def imsave(path: Path, array: np.ndarray, check_contrast: bool = False) -> None:
        import rasterio

        data = np.asarray(array)
        if data.ndim == 2:
            with rasterio.open(path, "w", driver="PNG", height=data.shape[0], width=data.shape[1], count=1, dtype=data.dtype) as dst:
                dst.write(data, 1)
        else:
            bands = np.transpose(data, (2, 0, 1))
            with rasterio.open(path, "w", driver="PNG", height=data.shape[0], width=data.shape[1], count=data.shape[2], dtype=data.dtype) as dst:
                dst.write(bands)

    def structural_similarity(a: np.ndarray, b: np.ndarray, data_range: float = 1.0) -> float:
        mse = float(np.mean((a - b) ** 2))
        return float(np.clip(1.0 - mse / max(data_range**2, 1e-6), 0.0, 1.0))

from stac_fetcher import SceneSummary, download_asset

WEIGHT_SSIM = 0.35
WEIGHT_SPECTRAL = 0.40
WEIGHT_RGB = 0.25

DEBUG_DIR = Path(__file__).resolve().parent / "demo" / "debug"
ASSET_CACHE_DIR = Path("/tmp/aegis_assets")
_VALID_EXTENSIONS = (".jp2", ".tif", ".tiff")
MAX_READ_DIM = int(os.getenv("AEGIS_MAX_BAND_DIM", "1024"))


def _ensure_debug_dir() -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    return DEBUG_DIR


def _normalize_band(arr: np.ndarray) -> np.ndarray:
    arr = arr.astype(np.float32)
    p2, p98 = np.nanpercentile(arr, [2, 98])
    if p98 <= p2:
        return np.clip(arr, 0, 1)
    return np.clip((arr - p2) / (p98 - p2), 0, 1)


def _read_single_band(path: Path, categorical: bool = False) -> np.ndarray:
    import rasterio
    from rasterio.enums import Resampling

    with rasterio.open(path) as src:
        height, width = src.height, src.width
        scale = min(1.0, float(MAX_READ_DIM) / max(height, width))
        if scale < 1.0:
            out_h = max(1, int(round(height * scale)))
            out_w = max(1, int(round(width * scale)))
            resampling = Resampling.nearest if categorical else Resampling.bilinear
            data = src.read(
                1,
                out_shape=(out_h, out_w),
                resampling=resampling,
            )
        else:
            data = src.read(1)
        return data.astype(np.float32)


def compute_simple_cloud_mask(scl_band: np.ndarray) -> np.ndarray:
    cloud_classes = np.array([8, 9, 10, 11])
    return np.isin(scl_band, cloud_classes)


def _download_band(scene_summary: SceneSummary, band: str) -> np.ndarray | None:
    if band not in scene_summary.assets:
        return None
    band_path = download_asset(scene_summary, band, ASSET_CACHE_DIR, DEBUG_DIR)
    return _read_single_band(band_path, categorical=(band == "SCL"))


def load_rgb_and_mask(scene_summary: SceneSummary) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Load RGB, cloud mask, and extra metadata arrays for a scene."""

    red = _download_band(scene_summary, "B04")
    green = _download_band(scene_summary, "B03")
    blue = _download_band(scene_summary, "B02")
    if red is None or green is None or blue is None:
        raise FileNotFoundError("Scene must include B04/B03/B02 assets")

    rgb = np.dstack((_normalize_band(red), _normalize_band(green), _normalize_band(blue))).astype(np.float32)

    scl = _download_band(scene_summary, "SCL")
    if scl is not None:
        cloud_mask = compute_simple_cloud_mask(scl)
    else:
        b8a = _download_band(scene_summary, "B8A")
        brightness = rgb.mean(axis=2)
        if b8a is not None:
            cloud_mask = _normalize_band(b8a) > 0.75
        else:
            cloud_mask = brightness > 0.85

    nir = _download_band(scene_summary, "B08")
    if nir is None:
        nir = _download_band(scene_summary, "B8A")
    meta = {
        "id": scene_summary.id,
        "red": red,
        "nir": None,
        "nir": nir,
        "nir_b8a": _download_band(scene_summary, "B8A"),
        "swir": _download_band(scene_summary, "B12"),
    }
    return rgb, cloud_mask.astype(bool), meta


def compute_rgb_diff(baseline_rgb: np.ndarray, recent_rgb: np.ndarray, mask: np.ndarray) -> float:
    diff = np.abs(recent_rgb - baseline_rgb).mean(axis=2)
    valid = ~mask
    if not np.any(valid):
        return 0.0
    return float(np.clip(np.mean(diff[valid]), 0.0, 1.0))


def compute_ssim_score(baseline_gray: np.ndarray, recent_gray: np.ndarray, mask: np.ndarray) -> float:
    valid = ~mask
    if not np.any(valid):
        return 0.0
    b = baseline_gray.copy()
    r = recent_gray.copy()
    fill_b = float(np.mean(b[valid]))
    fill_r = float(np.mean(r[valid]))
    b[~valid] = fill_b
    r[~valid] = fill_r
    ssim = structural_similarity(b, r, data_range=1.0)
    return float(np.clip(1.0 - ssim, 0.0, 1.0))


def _safe_index(numer: np.ndarray, denom: np.ndarray) -> np.ndarray:
    return numer / (denom + 1e-6)


def compute_spectral_delta(baseline_meta: dict[str, Any], recent_meta: dict[str, Any], mask: np.ndarray) -> float:
    b_nir_b8a = baseline_meta.get("nir_b8a")
    r_nir_b8a = recent_meta.get("nir_b8a")
    b_swir = baseline_meta.get("swir")
    r_swir = recent_meta.get("swir")

    if b_nir_b8a is not None and r_nir_b8a is not None and b_swir is not None and r_swir is not None:
        baseline_index = _safe_index((b_nir_b8a - b_swir), (b_nir_b8a + b_swir))
        recent_index = _safe_index((r_nir_b8a - r_swir), (r_nir_b8a + r_swir))
        mode = "NBR"
    else:
        b_nir = baseline_meta.get("nir")
        r_nir = recent_meta.get("nir")
        b_red = baseline_meta.get("red")
        r_red = recent_meta.get("red")
        if b_nir is None or r_nir is None or b_red is None or r_red is None:
            return 0.0
        baseline_index = _safe_index((b_nir - b_red), (b_nir + b_red))
        recent_index = _safe_index((r_nir - r_red), (r_nir + r_red))
        mode = "NDVI"

    valid = ~mask
    if not np.any(valid):
        return 0.0
    delta = np.abs(recent_index - baseline_index)
    scale = np.clip(np.mean(delta[valid]) / 2.0, 0.0, 1.0)
    return float(scale)


def urban_mask(rgb: np.ndarray, ndvi: np.ndarray | None) -> np.ndarray:
    brightness = rgb.mean(axis=2)
    if ndvi is not None:
        return (ndvi < 0.25) & (brightness > 0.25)
    return brightness > 0.4


def combine_scores(
    rgb_diff: float,
    ssim_delta: float,
    spectral_delta: float,
    weights: tuple[float, float, float] = (WEIGHT_SSIM, WEIGHT_SPECTRAL, WEIGHT_RGB),
) -> float:
    w_ssim, w_spectral, w_rgb = weights
    total = w_ssim + w_spectral + w_rgb
    if total <= 0:
        return 0.0
    score = (ssim_delta * w_ssim + spectral_delta * w_spectral + rgb_diff * w_rgb) / total
    return float(np.clip(score, 0.0, 1.0))


def analyze_scene_pair(baseline_scene: SceneSummary, recent_scene: SceneSummary) -> dict[str, Any]:
    """Run full analysis and emit debug artifacts."""

    debug_dir = _ensure_debug_dir()
    baseline_rgb, baseline_cloud, baseline_meta = load_rgb_and_mask(baseline_scene)
    recent_rgb, recent_cloud, recent_meta = load_rgb_and_mask(recent_scene)

    cloud_union = baseline_cloud | recent_cloud

    b_nir = baseline_meta.get("nir")
    b_red = baseline_meta.get("red")
    ndvi = _safe_index((b_nir - b_red), (b_nir + b_red)) if b_nir is not None and b_red is not None else None
    urban = urban_mask(recent_rgb, ndvi)
    analysis_mask = cloud_union | (~urban)

    baseline_gray = baseline_rgb.mean(axis=2)
    recent_gray = recent_rgb.mean(axis=2)
    rgb_diff = compute_rgb_diff(baseline_rgb, recent_rgb, analysis_mask)
    ssim_delta = compute_ssim_score(baseline_gray, recent_gray, analysis_mask)
    spectral_delta = compute_spectral_delta(baseline_meta, recent_meta, analysis_mask)
    final_score = max(combine_scores(rgb_diff, ssim_delta, spectral_delta), min(1.0, rgb_diff * 3.5), ssim_delta)

    return _save_debug_artifacts(
        baseline_rgb,
        recent_rgb,
        analysis_mask,
        rgb_diff,
        ssim_delta,
        spectral_delta,
        final_score,
        baseline_id=baseline_scene.id,
        recent_id=recent_scene.id,
    )


def cloud_mask_and_rgb(scene_path: str) -> tuple[np.ndarray, np.ndarray]:
    scene_dir = Path(scene_path)
    if not scene_dir.is_dir():
        scene_dir = scene_dir.parent

    def find(token: str) -> Path | None:
        files = [p for p in scene_dir.rglob("*") if p.suffix.lower() in _VALID_EXTENSIONS and token in p.stem]
        return sorted(files, key=lambda p: str(p))[0] if files else None

    b04 = find("B04")
    b03 = find("B03")
    b02 = find("B02")
    if b04 is None or b03 is None or b02 is None:
        raise FileNotFoundError("Missing required Sentinel-2 bands: B04, B03, B02")

    red = _read_single_band(b04)
    green = _read_single_band(b03)
    blue = _read_single_band(b02)
    rgb_array = np.dstack((red, green, blue)).astype(np.float32)

    scl = find("SCL")
    if scl is not None:
        cloud_mask = np.isin(_read_single_band(scl).astype(np.int16), [3, 8, 9, 10, 11])
    else:
        cloud_mask = np.zeros(red.shape, dtype=bool)
    return rgb_array, cloud_mask


def change_score(
    baseline_rgb: np.ndarray,
    recent_rgb: np.ndarray,
    cloud_mask_baseline: Optional[np.ndarray] = None,
    cloud_mask_recent: Optional[np.ndarray] = None,
) -> float:
    baseline = np.asarray(baseline_rgb, dtype=np.float32)
    recent = np.asarray(recent_rgb, dtype=np.float32)
    valid = np.ones(baseline.shape[:2], dtype=bool)
    if cloud_mask_baseline is not None:
        valid &= ~np.asarray(cloud_mask_baseline, dtype=bool)
    if cloud_mask_recent is not None:
        valid &= ~np.asarray(cloud_mask_recent, dtype=bool)
    if not np.any(valid):
        return 0.0
    diff = np.abs(recent.mean(axis=2) - baseline.mean(axis=2))
    return float(np.clip(np.mean(diff[valid]), 0.0, 1.0))


def detect_change_from_band_difference(
    before_band: np.ndarray,
    after_band: np.ndarray,
    change_threshold: float = 0.15,
) -> dict[str, float | bool]:
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


def _save_debug_artifacts(
    baseline_rgb: np.ndarray,
    recent_rgb: np.ndarray,
    analysis_mask: np.ndarray,
    rgb_diff: float,
    ssim_delta: float,
    spectral_delta: float,
    final_score: float,
    baseline_id: str,
    recent_id: str,
) -> dict[str, Any]:
    debug_dir = _ensure_debug_dir()
    diff_map = np.abs(recent_rgb - baseline_rgb).mean(axis=2)
    heatmap = exposure.rescale_intensity(diff_map, out_range=(0, 255)).astype(np.uint8)

    imsave(debug_dir / "baseline_rgb.png", (baseline_rgb * 255).astype(np.uint8), check_contrast=False)
    imsave(debug_dir / "recent_rgb.png", (recent_rgb * 255).astype(np.uint8), check_contrast=False)
    imsave(debug_dir / "diff_heatmap.png", heatmap, check_contrast=False)
    imsave(debug_dir / "mask.png", (analysis_mask.astype(np.uint8) * 255), check_contrast=False)

    metrics = {
        "baseline_id": baseline_id,
        "recent_id": recent_id,
        "rgb_diff": rgb_diff,
        "ssim_delta": ssim_delta,
        "spectral_delta": spectral_delta,
        "final_score": final_score,
    }
    (debug_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def analyze_sample_tiffs(baseline_tif: str | Path, recent_tif: str | Path) -> dict[str, Any]:
    """Analyze deterministic sample GeoTIFFs and emit standard debug artifacts."""
    import rasterio

    with rasterio.open(baseline_tif) as src:
        b = src.read([1, 2, 3]).astype(np.float32)
    with rasterio.open(recent_tif) as src:
        r = src.read([1, 2, 3]).astype(np.float32)

    baseline_rgb = np.transpose(b, (1, 2, 0))
    recent_rgb = np.transpose(r, (1, 2, 0))

    cloud_mask = np.zeros(baseline_rgb.shape[:2], dtype=bool)
    analysis_mask = cloud_mask

    rgb_diff = compute_rgb_diff(baseline_rgb, recent_rgb, analysis_mask)
    ssim_delta = compute_ssim_score(baseline_rgb.mean(axis=2), recent_rgb.mean(axis=2), analysis_mask)
    spectral_delta = float(np.clip(np.mean(np.abs(recent_rgb - baseline_rgb)[~analysis_mask]), 0.0, 1.0) * 2.0)
    final_score = max(combine_scores(rgb_diff, ssim_delta, spectral_delta), min(1.0, rgb_diff * 3.5), ssim_delta)

    return _save_debug_artifacts(
        baseline_rgb,
        recent_rgb,
        analysis_mask,
        rgb_diff,
        ssim_delta,
        spectral_delta,
        final_score,
        baseline_id=Path(baseline_tif).name,
        recent_id=Path(recent_tif).name,
    )
