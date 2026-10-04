"""
Repeated-Edit Error Accumulation Evaluation.

Evaluates multi-step sequential edits:
Step 0: Baseline (Single building 16x16x18m at center)
Step 1: Height increase (18m -> 24m)
Step 2: Building move (+10m X, +5m Y)
Step 3: Height decrease (24m -> 18m)
Step 4: Building removal
Step 5: Return to baseline (re-insert original building at original position and height)

Measures:
- Error drift across repeated incremental reuse
- Ground truth full recomputation at each step
- Comparison against original baseline at reversion step
- Soundness and certificate bound compliance
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
import time
from typing import List, Dict, Any, Tuple
import numpy as np

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.reference.full_recompute import full_recompute, SimulationResult
from urban_comfort.incremental.update import (
    AddBuildingEdit, RemoveBuildingEdit, ChangeHeightEdit, MoveBuildingEdit,
    incremental_update_certified
)
from urban_comfort.incremental.certificate import verify_certificate


@dataclass
class RepeatedEditRecord:
    step_number: int
    step_name: str
    edit_description: str
    full_runtime_sec: float
    incremental_runtime_sec: float
    speedup: float
    reused_cells: int
    recomputed_cells: int
    reused_fraction: float
    max_actual_error_k: float
    mean_actual_error_k: float
    max_predicted_bound_k: float
    baseline_reversion_error_k: float
    certificate_violations: int
    is_sound: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_repeated_edit_sequence(weather: Weather,
                               config: SimulationConfig) -> List[RepeatedEditRecord]:
    """
    Executes the canonical 5-step sequential editing sequence and tracks error accumulation.
    """
    records: List[RepeatedEditRecord] = []

    # Domain: 80m x 80m
    grid_cfg = PedestrianGridConfig(extent_x=80.0, extent_y=80.0, resolution=1.0, pedestrian_height=1.1)
    total_cells = int(grid_cfg.extent_x * grid_cfg.extent_y)

    # Step 0: Baseline Scene
    scene0 = Scene(pedestrian_grid=grid_cfg)
    bldg_orig = Building("bldg_target", BoundingBox2D(32.0, 48.0, 32.0, 48.0), height=18.0)
    scene0.add_building(bldg_orig)

    t0 = time.perf_counter()
    res0_full = full_recompute(scene0, weather, config)
    t0_time = time.perf_counter() - t0

    records.append(RepeatedEditRecord(
        step_number=0,
        step_name="baseline",
        edit_description="Initial central building (16x16x18m)",
        full_runtime_sec=t0_time,
        incremental_runtime_sec=t0_time,
        speedup=1.0,
        reused_cells=0,
        recomputed_cells=total_cells,
        reused_fraction=0.0,
        max_actual_error_k=0.0,
        mean_actual_error_k=0.0,
        max_predicted_bound_k=0.0,
        baseline_reversion_error_k=0.0,
        certificate_violations=0,
        is_sound=True
    ))

    current_scene = scene0
    current_inc_res = res0_full

    # Define the 5 sequential steps:
    # (step_num, step_name, edit_obj, description)
    edits = [
        (1, "height_increase", ChangeHeightEdit("bldg_target", 24.0), "Height increase: 18m -> 24m (+6m)"),
        (2, "building_move", MoveBuildingEdit("bldg_target", 10.0, 5.0), "Translation: +10m East, +5m North"),
        (3, "height_decrease", ChangeHeightEdit("bldg_target", 18.0), "Height decrease: 24m -> 18m (-6m)"),
        (4, "building_removal", RemoveBuildingEdit("bldg_target"), "Removal: Remove building completely"),
        (5, "return_to_baseline", AddBuildingEdit(Building("bldg_target", BoundingBox2D(32.0, 48.0, 32.0, 48.0), height=18.0)), "Return: Re-add initial building at original position")
    ]

    for step_num, step_name, edit, desc in edits:
        next_scene, _ = edit.apply(current_scene)

        # Ground truth full recomputation at this step
        t0 = time.perf_counter()
        next_full_res = full_recompute(next_scene, weather, config)
        t_full = time.perf_counter() - t0

        # Incremental update starting from previous step's incremental result
        t0 = time.perf_counter()
        inc_res, cert = incremental_update_certified(
            current_scene, next_scene, current_inc_res, edit, weather, config
        )
        t_inc = time.perf_counter() - t0

        verif = verify_certificate(cert, inc_res.result.tmrt, next_full_res.tmrt)
        err_step = np.abs(inc_res.result.tmrt - next_full_res.tmrt)

        # Reversion error (compared to initial Step 0 baseline if returning to baseline)
        if step_num == 5:
            reversion_err = float(np.max(np.abs(inc_res.result.tmrt - res0_full.tmrt)))
        else:
            reversion_err = float("nan")

        rec = RepeatedEditRecord(
            step_number=step_num,
            step_name=step_name,
            edit_description=desc,
            full_runtime_sec=t_full,
            incremental_runtime_sec=t_inc,
            speedup=t_full / t_inc if t_inc > 0 else 1.0,
            reused_cells=cert.reused_cells,
            recomputed_cells=cert.affected_cells,
            reused_fraction=cert.reused_fraction,
            max_actual_error_k=float(np.max(err_step)),
            mean_actual_error_k=float(np.mean(err_step)),
            max_predicted_bound_k=float(cert.max_predicted_bound),
            baseline_reversion_error_k=reversion_err,
            certificate_violations=verif.num_violations,
            is_sound=verif.is_valid
        )
        records.append(rec)

        # Advance state
        current_scene = next_scene
        current_inc_res = inc_res.result

    return records
