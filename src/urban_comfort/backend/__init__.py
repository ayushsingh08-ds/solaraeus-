"""
SOLARAEUS Simulation Backend Package.

Provides CPU and GPU execution backends with runtime selection and geometry flattening.
"""

from __future__ import annotations
from typing import Optional

from urban_comfort.backend.base import (
    SimulationBackend, FlattenedSceneGeometry, BackendProfileMetrics
)
from urban_comfort.backend.cpu_backend import CPUBackend
from urban_comfort.backend.gpu_backend import GPUBackend, is_cupy_available
from urban_comfort.backend.gpu_incremental import (
    GPUIncrementalEngine, GPUResidentState, GPUIncrementalProfileMetrics
)


def is_gpu_available() -> bool:
    """Returns True if a compatible CUDA GPU is available for simulation."""
    return is_cupy_available()


def get_backend(name: str = "cpu", fallback_to_cpu: bool = False) -> SimulationBackend:
    """
    Factory function returning the requested simulation backend.
    
    Parameters:
        name: 'cpu', 'gpu', or 'auto'.
        fallback_to_cpu: If True, falls back to CPUBackend when GPU is unavailable.
        
    Returns:
        SimulationBackend instance.
    """
    backend_key = name.lower().strip()
    if backend_key == "cpu":
        return CPUBackend()
    elif backend_key == "gpu":
        return GPUBackend(fallback_to_cpu=fallback_to_cpu)
    elif backend_key == "auto":
        if is_gpu_available():
            return GPUBackend(fallback_to_cpu=True)
        return CPUBackend()
    else:
        raise ValueError(f"Unknown simulation backend '{name}'. Must be 'cpu', 'gpu', or 'auto'.")


__all__ = [
    "SimulationBackend",
    "FlattenedSceneGeometry",
    "BackendProfileMetrics",
    "CPUBackend",
    "GPUBackend",
    "GPUIncrementalEngine",
    "GPUResidentState",
    "GPUIncrementalProfileMetrics",
    "is_gpu_available",
    "get_backend",
]

