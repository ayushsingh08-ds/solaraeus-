"""
Regression test locking the CPU-only guarantee when CuPy is absent (Track-2).

The GPU backend imports CuPy LAZILY (only inside execution methods), so the
package and every GPU-touching module must import cleanly on a machine with no
CuPy / no CUDA device, the CPU path must run, 'auto' must fall back to CPU, and
an EXPLICIT 'gpu' request must fail with a clean RuntimeError (never a bare
ImportError / ModuleNotFoundError leaking from a missing dependency).

CuPy absence is simulated in-process with a meta_path finder that blocks the
`cupy` import, so this test is meaningful on CI hosts that happen to have CuPy
installed as well as on those that do not.
"""

import contextlib
import importlib
import sys

import numpy as np
import pytest

from solaraeus.core.config import Weather, SimulationConfig
from solaraeus.core.geometry.scene import create_single_box_scene


class _BlockCupyFinder:
    """sys.meta_path finder that makes `import cupy` (and submodules) fail."""

    def find_spec(self, name, path, target=None):
        if name == "cupy" or name.startswith("cupy."):
            raise ImportError(f"CuPy blocked for test: {name}")
        return None


@contextlib.contextmanager
def cupy_absent():
    """Context manager simulating a host where CuPy cannot be imported."""
    finder = _BlockCupyFinder()
    saved_modules = {k: v for k, v in sys.modules.items()
                     if k == "cupy" or k.startswith("cupy.")}
    for k in saved_modules:
        del sys.modules[k]
    sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)
        sys.modules.update(saved_modules)


# GPU-touching modules that must import without CuPy installed.
_GPU_MODULES = [
    "solaraeus.backends.gpu",
    "solaraeus.backends.gpu_incremental",
    "solaraeus.backends",
    "solaraeus.extensions.terrain.gpu",
    "solaraeus.extensions.vegetation.gpu",
]


@pytest.fixture
def baseline_weather():
    return Weather(
        air_temperature_k=301.15, relative_humidity=50.0, wind_speed_ms=2.0,
        wind_direction_deg=180.0, direct_normal_irradiance_w_m2=800.0,
        diffuse_horizontal_irradiance_w_m2=160.0,
    )


@pytest.fixture
def baseline_config():
    return SimulationConfig(
        latitude_deg=40.7128, longitude_deg=-74.0060, date="2024-07-15",
        local_time="12:00:00", grid_resolution_m=1.0, sky_patch_configuration=16,
    )


def test_is_cupy_available_false_when_blocked():
    """is_cupy_available / is_gpu_available report False under CuPy absence."""
    with cupy_absent():
        from solaraeus.backends.gpu import is_cupy_available
        from solaraeus.backends import is_gpu_available
        assert is_cupy_available() is False
        assert is_gpu_available() is False


def test_gpu_modules_import_cleanly_without_cupy():
    """Every GPU-touching module re-imports cleanly with CuPy blocked."""
    with cupy_absent():
        for mod_name in _GPU_MODULES:
            saved = sys.modules.pop(mod_name, None)
            try:
                importlib.import_module(mod_name)
            except (ImportError, ModuleNotFoundError) as exc:  # pragma: no cover
                pytest.fail(f"{mod_name} failed to import without CuPy: {exc}")
            finally:
                if saved is not None:
                    sys.modules[mod_name] = saved


def test_cpu_full_recompute_runs_without_cupy(baseline_weather, baseline_config):
    """The CPU reference path produces finite output with CuPy blocked."""
    with cupy_absent():
        from solaraeus.reference.full_recompute import full_recompute
        scene = create_single_box_scene(extent_m=60.0, box_size=14.0, box_height=18.0)
        result = full_recompute(scene, baseline_weather, baseline_config, backend="cpu")
        assert np.all(np.isfinite(result.tmrt))
        assert np.all(np.isfinite(result.utci))


def test_auto_backend_falls_back_to_cpu_without_cupy():
    """get_backend('auto') yields a CPU backend when no GPU is available."""
    with cupy_absent():
        from solaraeus.backends import get_backend, CPUBackend
        assert isinstance(get_backend("auto"), CPUBackend)


def test_explicit_gpu_raises_clean_runtimeerror(baseline_weather, baseline_config):
    """An explicit 'gpu' request fails with RuntimeError, not a bare ImportError."""
    with cupy_absent():
        from solaraeus.reference.full_recompute import full_recompute
        scene = create_single_box_scene(extent_m=60.0, box_size=14.0, box_height=18.0)
        with pytest.raises(RuntimeError):
            full_recompute(scene, baseline_weather, baseline_config, backend="gpu")
