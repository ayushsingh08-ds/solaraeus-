"""
Adversarial test suite execution with pytest.
Ensures zero certificate violations under adversarial edge conditions:
- Low sun angle (long stretched shadows)
- Perpendicular wide walls
- Hidden-surface occlusion reveal
- Dense urban canyon infill
- Building translation
"""

import pytest
from solaraeus.benchmark.adversarial import create_adversarial_suite
from solaraeus.benchmark.runner import run_experiment


@pytest.fixture(scope="module")
def adversarial_cases():
    return create_adversarial_suite(grid_size=60, dx=1.0)


@pytest.mark.parametrize("case_idx", [0, 1, 2, 3, 4])
def test_adversarial_case_soundness(adversarial_cases, case_idx):
    case = adversarial_cases[case_idx]
    # Fast test configuration for pytest
    case.config = case.config.__class__(num_azimuth_svf=16, max_search_dist_m=50.0)

    rec = run_experiment(
        initial_grid=case.grid,
        edit=case.edit,
        weather=case.weather,
        config=case.config,
        tolerance_k=0.5,
        case_name=case.name
    )

    assert rec.is_sound, (
        f"Adversarial case '{case.name}' produced {rec.num_violations} violations! "
        f"Max violation: {rec.max_violation_k:.6e} K"
    )
    assert rec.is_within_tolerance, (
        f"Adversarial case '{case.name}' violated user tolerance contract on reused cells!"
    )
