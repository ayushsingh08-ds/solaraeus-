"""
Configuration schema for the SOLARAEUS segregated microclimate pipeline & engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class PipelineConfig:
    """End-to-end execution settings for SOLARAEUS engine & segregated directories."""

    area: str = "berlin"
    timestamp: Optional[str] = None
    input_dir: Optional[Path] = None
    processed_dir: Optional[Path] = None
    optimized_dir: Optional[Path] = None
    grid_resolution_m: float = 2.0
    use_gpu: bool = False
    
    # Intervention & Optimization options
    num_shades: int = 2
    canopy_width_m: float = 4.0
    canopy_length_m: float = 8.0
    canopy_height_m: float = 4.0
    transmissivity: float = 0.10
    optimization_strategy: str = "max_pedestrian_cooling"

    stages_to_run: List[int] = field(default_factory=lambda: [1, 2, 3, 4, 5])
    tolerance_epsilon_k: float = 0.05
    n_optimization_evaluations: int = 50
    verbose: bool = True

    # Legacy compatibility aliases
    data_dir: Optional[Path] = None
    output_dir: Optional[Path] = None

    def __post_init__(self):
        root = Path(__file__).resolve().parent.parent.parent.parent
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Resolve unified input directory: data/input/<area>
        if self.input_dir is None:
            if self.data_dir is not None:
                self.input_dir = Path(self.data_dir)
            elif (root / "data" / "input" / self.area).exists():
                self.input_dir = root / "data" / "input" / self.area
            elif (root / "data" / "raw" / self.area).exists():
                self.input_dir = root / "data" / "raw" / self.area
            elif (root / "data" / self.area).exists():
                self.input_dir = root / "data" / self.area
            else:
                self.input_dir = root / "data" / "input" / self.area
        self.input_dir = Path(self.input_dir)
        self.data_dir = self.input_dir

        # Resolve segregated processed directory: data/processed/<area>/<timestamp>
        if self.processed_dir is None:
            if self.output_dir is not None:
                self.processed_dir = Path(self.output_dir)
            else:
                self.processed_dir = root / "data" / "processed" / self.area / self.timestamp
        self.processed_dir = Path(self.processed_dir)
        self.output_dir = self.processed_dir

        # Resolve segregated optimized directory: data/optimized/<area>/<timestamp>
        if self.optimized_dir is None:
            self.optimized_dir = root / "data" / "optimized" / self.area / self.timestamp
        self.optimized_dir = Path(self.optimized_dir)
