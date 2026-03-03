"""Generate deterministic sample GeoTIFFs for demo and CI usage."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


def generate_sample_tiffs(output_dir: str | Path = "demo") -> tuple[Path, Path]:
    """Create deterministic baseline/recent sample GeoTIFFs with synthetic damage."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    baseline_path = out / "sample_baseline.tif"
    recent_path = out / "sample_recent.tif"

    h, w = 128, 128
    rng = np.random.default_rng(42)
    base = np.clip(0.35 + 0.03 * rng.standard_normal((h, w, 3)), 0.0, 1.0).astype(np.float32)
    recent = base.copy()

    # Synthetic damage patch with sharp structural/spectral shift.
    recent[24:104, 24:104, 0] = 1.0
    recent[24:104, 24:104, 1] = 0.0
    recent[24:104, 24:104, 2] = 0.0

    transform = from_origin(0, 0, 10, 10)
    profile = {
        "driver": "GTiff",
        "height": h,
        "width": w,
        "count": 3,
        "dtype": rasterio.float32,
        "transform": transform,
        "crs": "EPSG:4326",
    }

    with rasterio.open(baseline_path, "w", **profile) as dst:
        for idx in range(3):
            dst.write(base[:, :, idx], idx + 1)

    with rasterio.open(recent_path, "w", **profile) as dst:
        for idx in range(3):
            dst.write(recent[:, :, idx], idx + 1)

    return baseline_path, recent_path


if __name__ == "__main__":
    b, r = generate_sample_tiffs()
    print(f"Wrote {b} and {r}")
