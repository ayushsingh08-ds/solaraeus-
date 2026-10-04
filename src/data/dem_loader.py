"""
SRTM 30m Digital Elevation Model (DEM) Loader.
Downloads NASA SRTM tile (N40W075), decompresses, reprojects to UTM EPSG:32618,
and resamples to a 1-meter ground elevation raster.
"""

import gzip
import logging
import math
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject
import requests

from src.config import ProjectConfig, StudyArea

logger = logging.getLogger(__name__)

SKADI_BASE_URL = "https://elevation-tiles-prod.s3.amazonaws.com/skadi"


def get_srtm_tile_name(lat: float, lon: float) -> str:
    """
    Computes standard 1-degree SRTM HGT tile name from latitude and longitude.
    Example: (40.7308, -73.9975) -> N40W074
             (40.7080, -74.0120) -> N40W075
    """
    lat_card = "N" if lat >= 0 else "S"
    lon_card = "E" if lon >= 0 else "W"
    lat_val = int(math.floor(abs(lat))) if lat >= 0 else int(math.ceil(abs(lat)))
    lon_val = int(math.ceil(abs(lon))) if lon < 0 else int(math.floor(abs(lon)))
    return f"{lat_card}{lat_val:02d}{lon_card}{lon_val:03d}"


def download_srtm_tile(tile_name: str, output_path: Path) -> None:
    """Downloads and decompresses the 30m SRTM HGT tile from AWS Skadi terrain repository."""
    lat_dir = tile_name[:3]  # e.g. "N40"
    url = f"{SKADI_BASE_URL}/{lat_dir}/{tile_name}.hgt.gz"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading SRTM tile {tile_name} from {url}...")
    response = requests.get(url, timeout=120)
    response.raise_for_status()

    raw_hgt = gzip.decompress(response.content)
    output_path.write_bytes(raw_hgt)
    logger.info(f"Saved decompressed HGT tile to {output_path} ({len(raw_hgt):,} bytes)")


def load_dem(
    config: Optional[ProjectConfig] = None,
    study_area: Optional[StudyArea] = None,
    force_download: bool = False,
    make_relative: bool = False,
) -> Tuple[np.ndarray, rasterio.Affine]:
    """
    Downloads SRTM tile if necessary, reprojects to target UTM zone, and resamples to 1m.

    Args:
        config: Project configuration.
        study_area: Target study area. Defaults to config.study_area.
        force_download: If True, re-downloads even if tile exists.
        make_relative: If True, subtracts minimum elevation so base is 0m.

    Returns:
        (dem_array, dst_transform):
            dem_array: (H, W) float32 array in meters.
            dst_transform: Affine transform mapping pixel coords to UTM coordinates.
    """
    if config is None:
        config = ProjectConfig()
    if study_area is None:
        study_area = config.study_area

    config.data.ensure_dirs()

    tile_name = get_srtm_tile_name(study_area.lat_center, study_area.lon_center)
    hgt_path = config.data.raw_dir / f"{tile_name}.hgt"
    safe_name = study_area.name.lower().replace(" ", "_").replace("/", "_")
    processed_tif_path = config.data.processed_dir / f"{safe_name}_dem_utm_1m.tif"

    if not hgt_path.exists() or force_download:
        download_srtm_tile(tile_name, hgt_path)

    utm_bounds = study_area.utm_bounds
    resolution_m = study_area.resolution_m
    dst_crs = CRS.from_epsg(study_area.utm_zone)

    # Calculate raster dimensions from bounds
    dst_width = int(round((utm_bounds[2] - utm_bounds[0]) / resolution_m))
    dst_height = int(round((utm_bounds[3] - utm_bounds[1]) / resolution_m))

    dst_transform = from_bounds(
        *utm_bounds,
        dst_width,
        dst_height,
    )

    dem_utm_1m = np.empty((dst_height, dst_width), dtype=np.float32)

    with rasterio.open(hgt_path) as src:
        logger.info(f"Source DEM CRS: {src.crs}, Shape: {src.shape}")
        reproject(
            source=rasterio.band(src, 1),
            destination=dem_utm_1m,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=Resampling.bilinear,
        )

    # Clean potential nodata values from SRTM (-32768)
    dem_utm_1m[dem_utm_1m < -100] = np.nan
    valid_mask = np.isfinite(dem_utm_1m)
    if not np.all(valid_mask):
        median_val = np.nanmedian(dem_utm_1m)
        dem_utm_1m[~valid_mask] = median_val

    if make_relative:
        min_elev = float(np.nanmin(dem_utm_1m))
        dem_utm_1m = dem_utm_1m - min_elev
        logger.info(f"Adjusted DEM to relative height (subtracted {min_elev:.2f}m)")

    # Save processed GeoTIFF for downstream caching
    with rasterio.open(
        processed_tif_path,
        "w",
        driver="GTiff",
        height=dst_height,
        width=dst_width,
        count=1,
        dtype=rasterio.float32,
        crs=dst_crs,
        transform=dst_transform,
    ) as dst:
        dst.write(dem_utm_1m, 1)

    logger.info(
        f"Processed DEM saved to {processed_tif_path}: "
        f"shape=({dst_height}, {dst_width}), min={dem_utm_1m.min():.2f}m, max={dem_utm_1m.max():.2f}m"
    )

    return dem_utm_1m, dst_transform


# Convenience alias for the documented public API
load = load_dem
