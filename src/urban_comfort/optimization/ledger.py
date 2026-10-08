"""
Candidate Database & Evaluation Ledger.

Maintains an immutable record of all proposed candidate interventions,
their parameters, geographic feasibility outcomes, simulation runtimes,
certificate verification results, and thermal comfort objective scores.
"""

from __future__ import annotations
import csv
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from urban_comfort.optimization.parameters import ShadePanelParams
from urban_comfort.optimization.feasibility import FeasibilityResult
from urban_comfort.optimization.objective import EvaluationMetrics


@dataclass
class CandidateRecord:
    """Comprehensive ledger entry for an intervention proposal."""
    candidate_id: str
    iteration: int
    method: str                              # "deterministic_baseline", "random", "lhs", "evolutionary"
    params: Dict[str, float]
    is_feasible: bool
    rejection_reason: Optional[str] = None
    rejection_message: Optional[str] = None
    objective_value: float = float("inf")
    metrics: Optional[Dict[str, Any]] = None
    gpu_metrics: Optional[Dict[str, Any]] = None
    certificate_status: Optional[str] = None
    certificate_violations: Optional[int] = None
    max_predicted_bound_k: Optional[float] = None
    wall_time_s: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "iteration": self.iteration,
            "method": self.method,
            "params": self.params,
            "is_feasible": self.is_feasible,
            "rejection_reason": self.rejection_reason,
            "rejection_message": self.rejection_message,
            "objective_value": float(self.objective_value) if math_isfinite(self.objective_value) else None,
            "metrics": self.metrics,
            "gpu_metrics": self.gpu_metrics,
            "certificate_status": self.certificate_status,
            "certificate_violations": self.certificate_violations,
            "max_predicted_bound_k": self.max_predicted_bound_k,
            "wall_time_s": round(self.wall_time_s, 4),
        }


def math_isfinite(val: float) -> bool:
    import math
    return math.isfinite(val)


class CandidateLedger:
    """In-memory database and exporter for optimization history."""

    def __init__(self):
        self.records: List[CandidateRecord] = []

    def add(self, record: CandidateRecord):
        """Appends a candidate evaluation record."""
        self.records.append(record)

    def __len__(self) -> int:
        return len(self.records)

    def get_feasible(self) -> List[CandidateRecord]:
        """Returns all geographically feasible candidates."""
        return [r for r in self.records if r.is_feasible]

    def get_rejected(self) -> List[CandidateRecord]:
        """Returns all rejected candidates."""
        return [r for r in self.records if not r.is_feasible]

    def get_best(self) -> Optional[CandidateRecord]:
        """Returns the feasible candidate with the lowest objective value."""
        feasible = self.get_feasible()
        if not feasible:
            return None
        return min(feasible, key=lambda r: r.objective_value)

    def get_top_n(self, n: int = 5) -> List[CandidateRecord]:
        """Returns the top N feasible candidates ordered by objective improvement."""
        feasible = self.get_feasible()
        feasible_sorted = sorted(feasible, key=lambda r: r.objective_value)
        return feasible_sorted[:n]

    def save_json(self, path: Path):
        """Serializes ledger to JSON file."""
        data = [r.to_dict() for r in self.records]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def save_csv(self, path: Path):
        """Exports tabular summary of candidates to CSV."""
        if not self.records:
            return

        rows: List[Dict[str, Any]] = []
        for r in self.records:
            p = r.params
            m = r.metrics or {}
            gm = r.gpu_metrics or {}
            rows.append({
                "candidate_id": r.candidate_id,
                "iteration": r.iteration,
                "method": r.method,
                "is_feasible": r.is_feasible,
                "rejection_reason": r.rejection_reason or "",
                "objective_value": r.objective_value if math_isfinite(r.objective_value) else "",
                "x": p.get("x", ""),
                "y": p.get("y", ""),
                "length": p.get("length", ""),
                "width": p.get("width", ""),
                "height": p.get("height", ""),
                "heading_deg": p.get("heading_deg", ""),
                "albedo": p.get("albedo", ""),
                "area_m2": p.get("area_m2", ""),
                "mean_utci_c": m.get("mean_utci_c", ""),
                "p90_utci_c": m.get("p90_utci_c", ""),
                "pct_improved_cells": m.get("pct_improved_cells", ""),
                "delta_mean_utci_c": m.get("delta_mean_utci_c", ""),
                "recomputed_cells": gm.get("recomputed_cells", ""),
                "reused_cells": gm.get("reused_cells", ""),
                "ray_work_reduction_pct": gm.get("ray_work_reduction_pct", ""),
                "gpu_kernel_time_ms": gm.get("gpu_kernel_time_ms", ""),
                "certificate_violations": r.certificate_violations if r.certificate_violations is not None else "",
                "wall_time_s": r.wall_time_s,
            })

        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
