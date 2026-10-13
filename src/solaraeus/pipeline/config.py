"""
Configuration schema for the SOLARAEUS 5-stage microclimate pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class PipelineConfig:
    """End-to-end execution settings for SOLARAEUS pipeline."""

    area: str = "church_street"
    data_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    grid_resolution_m: float = 2.0
    use_gpu: bool = False
    stages_to_run: List[int] = field(default_factory=lambda: [1, 2, 3, 4, 5])
    tolerance_epsilon_k: float = 0.05
    n_optimization_evaluations: int = 50
    verbose: bool = True

    def __post_init__(self):
        root = Path(__file__).resolve().parent.parent.parent.parent
        if self.data_dir is None:
            self.data_dir = root / "data" / self.area
        if self.output_dir is None:
            self.output_dir = root / "results" / f"{self.area}_pipeline"
        self.data_dir = Path(self.data_dir)
        self.output_dir = Path(self.output_dir)
