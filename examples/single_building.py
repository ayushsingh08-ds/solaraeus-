"""
Example: Running full reference microclimate simulation on a single building scene.
"""

import os
import sys
import numpy as np

# Ensure src is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.scene import Scene
from urban_comfort.reference.full_recompute import full_recompute
from urban_comfort.comfort.utci import get_thermal_stress_category


def run_single_building_example():
    print("=" * 75)
    print("URBAN COMFORT: SINGLE BUILDING REFERENCE RECOMPUTATION EXAMPLE")
    print("=" * 75)

    config_path = os.path.join(os.path.dirname(__file__), "..", "configs", "baseline_scene.json")
    print(f"Loading scene configuration from: {config_path}")
    scene = Scene.load_json(config_path)

    weather = Weather(
        air_temperature=301.15,           # 28 C
        relative_humidity=50.0,
        wind_speed=2.0,                   # 2 m/s
        wind_direction=180.0,
        direct_normal_irradiance=800.0,   # 800 W/m^2
        diffuse_horizontal_irradiance=160.0
    )

    config = SimulationConfig(
        latitude=40.7128,
        longitude=-74.0060,
        date="2024-07-15",
        local_time="12:00:00",
        grid_resolution=1.0,
        sky_patch_configuration=32
    )

    print(f"Simulating location: ({config.latitude} N, {config.longitude} E) at {config.date} {config.local_time} UTC")
    result = full_recompute(scene, weather, config)

    meta = result.metadata
    print(f"Solar Altitude: {meta['solar_altitude_deg']:.2f} deg, Azimuth: {meta['solar_azimuth_deg']:.2f} deg")
    print(f"Total Grid Cells: {meta['total_cells']}")

    # Statistics
    lit_cells = np.sum(result.shadow_mask == 1.0)
    shade_cells = np.sum(result.shadow_mask == 0.0)
    print(f"Illuminated Cells: {lit_cells} ({lit_cells/meta['total_cells']*100:.1f}%)")
    print(f"Shaded Cells: {shade_cells} ({shade_cells/meta['total_cells']*100:.1f}%)")

    mean_tmrt_lit = np.mean(result.tmrt[result.shadow_mask == 1.0])
    mean_tmrt_shade = np.mean(result.tmrt[result.shadow_mask == 0.0])
    print(f"Mean T_mrt (Sunlit): {mean_tmrt_lit:.2f} C")
    print(f"Mean T_mrt (Shaded): {mean_tmrt_shade:.2f} C (Delta: {mean_tmrt_lit - mean_tmrt_shade:.2f} K)")

    mean_utci = np.mean(result.utci)
    stress_cat = get_thermal_stress_category(float(mean_utci))
    print(f"Mean UTCI: {mean_utci:.2f} C ({stress_cat})")

    print("\nExecution Timing Breakdown:")
    print(f"  - Direct Shadow Raycasting: {meta['timing_shadow_sec']*1000:.2f} ms")
    print(f"  - Sky View Factor (SVF):   {meta['timing_svf_sec']*1000:.2f} ms")
    print(f"  - Radiative Fluxes & Tmrt: {meta['timing_radiation_sec']*1000:.2f} ms")
    print(f"  - Thermal Comfort (UTCI):  {meta['timing_utci_sec']*1000:.2f} ms")
    print(f"  - Total End-to-End:        {meta['timing_total_sec']*1000:.2f} ms")
    print("=" * 75)


if __name__ == "__main__":
    run_single_building_example()
