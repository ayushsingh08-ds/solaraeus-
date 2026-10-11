"""Golden-master scenario definitions (Track-1 behaviour-preserving baseline).

ALL engine imports live in this module. When Track-1 renames the package
(`urban_comfort` -> `solaraeus`) or moves modules, update the imports HERE in the
same commit; the frozen baseline numbers under ``baseline/`` must never change.

Each scenario returns ``(arrays, scalars)``:
  * arrays  -> dict[str, np.ndarray]  (compared bitwise/rtol=1e-9; masks exact)
  * scalars -> dict[str, float|int|bool|str]

Timings are deliberately excluded (non-deterministic).
"""
from __future__ import annotations

import os
import sys

import numpy as np

# Force the WORKTREE src onto the path HEAD. An editable install
# (_editable_impl_solaraeus.pth) otherwise resolves the package to the main
# checkout, which would make the baseline test the wrong tree.
_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if sys.path and sys.path[0] != _SRC:
    sys.path.insert(0, _SRC)

from solaraeus.core.config import Weather, SimulationConfig  # noqa: E402
from solaraeus.core.geometry.primitives import Building, BoundingBox2D  # noqa: E402
from solaraeus.core.geometry.scene import Scene, PedestrianGridConfig  # noqa: E402
from solaraeus.reference.full_recompute import full_recompute  # noqa: E402
from solaraeus.incremental.update import AddBuildingEdit, incremental_update_certified  # noqa: E402
from solaraeus.incremental.certificate import verify_certificate  # noqa: E402

_CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "configs"))

# --- shared deterministic boundary conditions (mirror examples/) -------------
_WEATHER = dict(
    air_temperature_k=301.15, relative_humidity=50.0, wind_speed_ms=2.0,
    wind_direction_deg=180.0, direct_normal_irradiance_w_m2=800.0,
    diffuse_horizontal_irradiance_w_m2=160.0,
)


def _to_numpy(a):
    """Host numpy view, tolerant of cupy device arrays from the GPU backend."""
    if a is None:
        return None
    if hasattr(a, "get") and not isinstance(a, np.ndarray):
        return np.asarray(a.get())
    return np.asarray(a)


def _result_arrays(res) -> dict:
    return {
        "shadow_mask": _to_numpy(res.shadow_mask),
        "direct_irradiance": _to_numpy(res.direct_irradiance),
        "svf": _to_numpy(res.svf),
        "shortwave_flux": _to_numpy(res.shortwave_flux),
        "longwave_flux": _to_numpy(res.longwave_flux),
        "tmrt": _to_numpy(res.tmrt),
        "utci": _to_numpy(res.utci),
    }


def _result_scalars(res, prefix: str) -> dict:
    m = res.metadata
    out = {}
    for k in ("solar_altitude_deg", "solar_azimuth_deg", "solar_zenith_deg",
              "is_daylight", "num_buildings", "total_cells", "air_temperature_c"):
        if k in m:
            out[f"{prefix}{k}"] = m[k]
    return out


def _single_building(backend: str):
    scene = Scene.load_json(os.path.join(_CONFIG_DIR, "baseline_scene.json"))
    weather = Weather(**_WEATHER)
    config = SimulationConfig(
        latitude=40.7128, longitude=-74.0060, date="2024-07-15",
        local_time="12:00:00", grid_resolution=1.0, sky_patch_configuration=32,
    )
    res = full_recompute(scene, weather, config, backend=backend)
    return _result_arrays(res), _result_scalars(res, "")


def _incremental(backend: str):
    weather = Weather(**_WEATHER)
    config = SimulationConfig(
        latitude=40.7128, longitude=-74.0060, date="2024-07-15",
        local_time="12:00:00", grid_resolution=1.0, sky_patch_configuration=16,
        max_svf_search_dist_m=30.0, tmrt_tolerance_k=0.5,
    )
    grid_cfg = PedestrianGridConfig(extent_x=80.0, extent_y=80.0, resolution=1.0, pedestrian_height=1.1)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_building(Building("bldg_center", BoundingBox2D(32.0, 48.0, 32.0, 48.0), height=18.0))

    base_res = full_recompute(scene_base, weather, config, backend=backend)
    edit = AddBuildingEdit(Building("bldg_infill", BoundingBox2D(14.0, 28.0, 46.0, 60.0), height=15.0))
    scene_edit, _ = edit.apply(scene_base)
    full_res = full_recompute(scene_edit, weather, config, backend=backend)
    inc_res, cert = incremental_update_certified(scene_base, scene_edit, base_res, edit, weather, config, backend=backend)
    inc = inc_res.result
    verif = verify_certificate(cert, inc.tmrt, full_res.tmrt)

    arrays = {}
    for name, res in (("base", base_res), ("full", full_res), ("inc", inc)):
        for k, v in _result_arrays(res).items():
            arrays[f"{name}__{k}"] = v
    arrays["cert_bound"] = _to_numpy(cert.predicted_error_bound_k)
    arrays["reused_mask"] = _to_numpy(cert.predicted_error_bound_k) <= cert.tolerance
    arrays["dirty_mask"] = _to_numpy(cert.predicted_error_bound_k) > cert.tolerance

    scalars = {
        "cert_status": cert.status,
        "cert_tolerance": float(cert.tolerance),
        "cert_total_cells": int(cert.total_cells),
        "cert_reused_cells": int(cert.reused_cells),
        "cert_affected_cells": int(cert.affected_cells),
        "cert_reused_fraction": float(cert.reused_fraction),
        "cert_max_predicted_bound": float(cert.max_predicted_bound_k),
        "verify_is_valid": bool(verif.is_valid),
        "verify_num_violations": int(verif.num_violations),
        "verify_reused_max_error": float(verif.reused_max_error),
        "verify_is_within_tolerance": bool(verif.is_within_tolerance),
        "verify_max_violation": float(verif.max_violation),
        "verify_min_slack": float(np.min(_to_numpy(verif.slack_map))),
    }
    scalars.update(_result_scalars(base_res, "base__"))
    return arrays, scalars


# name -> (builder, requires_gpu)
SCENARIOS = {
    "single_building_cpu": (lambda: _single_building("cpu"), False),
    "incremental_cpu": (lambda: _incremental("cpu"), False),
    "single_building_gpu": (lambda: _single_building("gpu"), True),
    "incremental_gpu": (lambda: _incremental("gpu"), True),
}
