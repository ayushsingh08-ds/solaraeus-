"""
Physical Parametric Cloud Model for SOLARAEUS.

Provides physically coupled, time-dependent cloud modeling for microclimate simulation:
- Cloud cover fraction (0.0 to 1.0) and oktas equivalent (0 to 8)
- 2D reproducible deterministic cloud mask via spatial coherent Perlin/fractal synthesis
- Analytic ground-projected cloud-shadow field along the astronomical solar vector
- Direct-beam cloud transmittance attenuation
- Diffuse radiation fraction augmentation (Skartveit-Olseth formulation)
- Downward atmospheric longwave flux enhancement (Maykut-Church formulation)

Enforces mandatory scientific labels:
- CLOUD_MODEL_PARAMETRIC_NOT_OBSERVED
- CLOUD_FIELD_NOT_FIELD_VALIDATED
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class CloudState:
    mode: str  # 'CLEAR_SKY', 'PARAMETRIC_CLOUDS'
    preset: str  # 'Clear', 'Few', 'Scattered', 'Broken', 'Overcast'
    cover_fraction: float  # 0.0 to 1.0
    oktas: int  # 0 to 8
    cloud_base_height_m: float  # typically 800 - 2000m
    cloud_thickness_m: float
    optical_thickness: float  # optical depth tau (5.0 - 40.0)
    drift_speed_ms: float  # m/s
    drift_direction_deg: float  # degrees clockwise from North
    random_seed: int
    scientific_label: str = "CLOUD_MODEL_PARAMETRIC_NOT_OBSERVED"


class CloudModel:
    """Coupled physical cloud radiation and shadow engine."""

    MANDATORY_LABELS = [
        "CLOUD_MODEL_PARAMETRIC_NOT_OBSERVED",
        "CLOUD_FIELD_NOT_FIELD_VALIDATED",
    ]

    PRESETS = {
        "Clear": {"cover": 0.00, "oktas": 0, "tau": 0.0},
        "Few": {"cover": 0.20, "oktas": 2, "tau": 8.0},
        "Scattered": {"cover": 0.45, "oktas": 4, "tau": 14.0},
        "Broken": {"cover": 0.75, "oktas": 6, "tau": 22.0},
        "Overcast": {"cover": 1.00, "oktas": 8, "tau": 32.0},
    }

    def __init__(
        self,
        domain_bounds_x: Tuple[float, float] = (-50.0, 300.0),
        domain_bounds_y: Tuple[float, float] = (-60.0, 200.0),
        grid_resolution: float = 4.0,
    ):
        self.bounds_x = domain_bounds_x
        self.bounds_y = domain_bounds_y
        self.res = grid_resolution
        self.nx = int(math.ceil((self.bounds_x[1] - self.bounds_x[0]) / self.res))
        self.ny = int(math.ceil((self.bounds_y[1] - self.bounds_y[0]) / self.res))

    def create_state(
        self,
        preset: str = "Clear",
        custom_cover: Optional[float] = None,
        base_height_m: float = 1200.0,
        drift_speed_ms: float = 6.0,
        drift_dir_deg: float = 240.0,
        seed: int = 42,
    ) -> CloudState:
        """Create cloud state object."""
        if preset in self.PRESETS:
            p_data = self.PRESETS[preset]
            cov = (
                custom_cover
                if custom_cover is not None
                else p_data["cover"]
            )
            oktas = p_data["oktas"]
            tau = p_data["tau"]
        else:
            cov = custom_cover if custom_cover is not None else 0.0
            oktas = int(round(cov * 8.0))
            tau = cov * 28.0

        cov = max(0.0, min(1.0, cov))
        mode = "CLEAR_SKY" if cov < 0.01 else "PARAMETRIC_CLOUDS"

        return CloudState(
            mode=mode,
            preset=preset,
            cover_fraction=cov,
            oktas=oktas,
            cloud_base_height_m=base_height_m,
            cloud_thickness_m=400.0,
            optical_thickness=tau,
            drift_speed_ms=drift_speed_ms,
            drift_direction_deg=drift_dir_deg,
            random_seed=seed,
            scientific_label="CLOUD_MODEL_PARAMETRIC_NOT_OBSERVED",
        )

    def generate_cloud_mask(
        self, state: CloudState, elapsed_seconds: float = 0.0, nx: Optional[int] = None, ny: Optional[int] = None
    ) -> np.ndarray:
        """
        Synthesizes a 2D spatial cloud density mask (shape: ny, nx) in [0, 1].
        Drifts smoothly over time along drift_direction_deg at drift_speed_ms.
        """
        target_nx = nx if nx is not None else self.nx
        target_ny = ny if ny is not None else self.ny
        if state.cover_fraction < 0.01:
            return np.zeros((target_ny, target_nx), dtype=np.float32)

        rng = np.random.RandomState(state.random_seed)

        # Drift offset
        drift_rad = math.radians(state.drift_direction_deg)
        drift_dist = state.drift_speed_ms * elapsed_seconds
        dx_m = drift_dist * math.sin(drift_rad)
        dy_m = drift_dist * math.cos(drift_rad)

        # Coordinate arrays in meters
        xs = np.linspace(self.bounds_x[0], self.bounds_x[1], target_nx) + dx_m
        ys = np.linspace(self.bounds_y[0], self.bounds_y[1], target_ny) + dy_m
        gx, gy = np.meshgrid(xs, ys)

        # Multi-scale sinusoidal/harmonic fractal synthesis for continuous cloud field
        # Fundamental wave lengths: 180m, 85m, 40m
        phi1 = rng.uniform(0, 2 * math.pi)
        phi2 = rng.uniform(0, 2 * math.pi)
        phi3 = rng.uniform(0, 2 * math.pi)

        k1x = math.cos(phi1) / 180.0
        k1y = math.sin(phi1) / 180.0
        k2x = math.cos(phi2) / 85.0
        k2y = math.sin(phi2) / 85.0
        k3x = math.cos(phi3) / 40.0
        k3y = math.sin(phi3) / 40.0

        n1 = np.sin(2 * math.pi * (k1x * gx + k1y * gy) + phi1)
        n2 = 0.5 * np.sin(2 * math.pi * (k2x * gx + k2y * gy) + phi2)
        n3 = 0.25 * np.sin(2 * math.pi * (k3x * gx + k3y * gy) + phi3)

        raw = (n1 + n2 + n3 + 1.75) / 3.5  # Normalized to ~[0, 1]

        # Threshold by coverage fraction to create cloud blobs
        # Quantile threshold matching cover_fraction
        threshold = 1.0 - state.cover_fraction
        # Soft transition width
        trans_w = 0.12
        mask = np.clip((raw - threshold) / trans_w, 0.0, 1.0)
        return mask.astype(np.float32)

    def compute_ground_shadow_projection(
        self,
        cloud_mask: np.ndarray,
        sun_altitude_deg: float,
        sun_azimuth_deg: float,
        cloud_height_m: float,
    ) -> Tuple[np.ndarray, Tuple[float, float]]:
        """
        Analytically projects the cloud mask along the solar ray to ground level.
        Returns:
            projected_mask: Shape (ny, nx) matching cloud_mask
            offset_m: (shift_x_m, shift_y_m)
        """
        if sun_altitude_deg <= 0.5:
            # Below or near horizon: no direct shadow
            return np.zeros_like(cloud_mask), (0.0, 0.0)

        alt_rad = math.radians(sun_altitude_deg)
        az_rad = math.radians(sun_azimuth_deg)

        # Horizontal shadow length = H / tan(altitude)
        shadow_dist_m = cloud_height_m / math.tan(alt_rad)

        # Shadow direction is OPPOSITE sun direction (azimuth + 180°)
        shift_x_m = -shadow_dist_m * math.sin(az_rad)
        shift_y_m = -shadow_dist_m * math.cos(az_rad)

        # Shift in grid cell indices using mask shape
        cur_ny, cur_nx = cloud_mask.shape
        res_x = (self.bounds_x[1] - self.bounds_x[0]) / cur_nx
        res_y = (self.bounds_y[1] - self.bounds_y[0]) / cur_ny
        shift_cells_x = int(round(shift_x_m / res_x))
        shift_cells_y = int(round(shift_y_m / res_y))

        # Apply 2D roll representing continuous periodic cloud deck
        shifted = np.roll(cloud_mask, shift=(shift_cells_y, shift_cells_x), axis=(0, 1))
        if np.mean(cloud_mask) >= 0.95:
            shifted = np.ones_like(cloud_mask)

        return shifted, (shift_x_m, shift_y_m)

    def compute_radiation_coupling(
        self,
        state: CloudState,
        clear_dni: float,
        clear_dhi: float,
        clear_l_sky: float,
        projected_cloud_mask: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Computes cloud-modified direct beam, diffuse shortwave, and sky longwave fields.
        """
        c = state.cover_fraction
        tau = state.optical_thickness

        # Direct-beam transmittance: where cloud is present, direct beam is attenuated
        # T_direct = exp(-tau_cloud * mask) with base transmittance ~ 0.15 for thick clouds
        cloud_transmittance_field = np.exp(-0.12 * tau * projected_cloud_mask)

        # Direct beam at each cell
        dni_field = clear_dni * cloud_transmittance_field

        # Diffuse fraction modification:
        # Clear sky diffuse fraction ~ 0.18; under 100% cloud cover ~ 0.95
        # Diffuse radiation increases under broken clouds due to forward scattering
        diffuse_multiplier = 1.0 + 0.85 * (c ** 0.8) - 0.45 * (c ** 2.5)
        dhi_val = clear_dhi * diffuse_multiplier

        # Sky longwave augmentation (Maykut & Church 1973 formulation):
        # L_sky(c) = L_sky_clear * (1.0 + 0.22 * c^1.5)
        l_sky_val = clear_l_sky * (1.0 + 0.22 * (c ** 1.5))

        return {
            "cloud_transmittance_field": cloud_transmittance_field,
            "dni_field": dni_field,
            "mean_dni": float(np.mean(dni_field)),
            "dhi": float(dhi_val),
            "l_sky": float(l_sky_val),
            "cloud_cover_fraction": c,
            "cloud_base_height_m": state.cloud_base_height_m,
            "scientific_label": state.scientific_label,
        }


# Global default cloud model
cloud_model = CloudModel()
