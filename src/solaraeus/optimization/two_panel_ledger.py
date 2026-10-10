"""
Two-Panel Candidate Database & Evaluation Ledger.

Maintains an immutable record of all proposed two-panel candidates,
their parameters, geographic feasibility outcomes, affected cell union/overlap metrics,
GPU incremental performance metrics, certificate verification results, and thermal comfort objective scores.
"""

from __future__ import annotations
import csv
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd


@dataclass
class TwoPanelCandidateRecord:
    """Comprehensive ledger entry for a two-panel intervention proposal."""
    candidate_id: str
    iteration: int
    method: str                              # "seed_best_offset", "seed_lhs", "surrogate_lcb", "random", etc.
    params: Dict[str, Any]                   # Dictionary containing panel1, panel2, total_area, etc.
    is_feasible: bool
    total_panel_area: float = 0.0
    rejection_reason: Optional[str] = None
    rejection_message: Optional[str] = None
    rejection_details: Optional[Dict[str, Any]] = None
    objective_value: float = float("inf")
    metrics: Optional[Dict[str, Any]] = None
    # Incremental spatial metrics
    affected_cells_count: Optional[int] = None
    recomputed_cells_count: Optional[int] = None
    reused_cells_count: Optional[int] = None
    total_active_cells: Optional[int] = None
    affected_rays_count: Optional[int] = None
    recomputed_rays_count: Optional[int] = None
    reused_rays_count: Optional[int] = None
    overlap_cells_count: Optional[int] = None
    union_cells_count: Optional[int] = None
    # GPU performance timings
    gpu_kernel_time_ms: Optional[float] = None
    host_to_device_time_ms: Optional[float] = None
    device_to_host_time_ms: Optional[float] = None
    total_runtime_s: float = 0.0
    wall_time_s: float = 0.0
    # Certificate validation
    certificate_status: Optional[str] = None
    certificate_violations: Optional[int] = None
    max_certificate_bound_k: Optional[float] = None
    max_observed_error_k: Optional[float] = None
    # Surrogate acquisition metadata
    surrogate_predicted_objective: Optional[float] = None
    surrogate_uncertainty: Optional[float] = None
    acquisition_strategy: Optional[str] = None
    total_panel_area_m2: Optional[float] = None

    def __post_init__(self):
        if self.total_panel_area_m2 is not None and self.total_panel_area == 0.0:
            self.total_panel_area = self.total_panel_area_m2
        if self.wall_time_s > 0.0 and self.total_runtime_s == 0.0:
            self.total_runtime_s = self.wall_time_s
        elif self.total_runtime_s > 0.0 and self.wall_time_s == 0.0:
            self.wall_time_s = self.total_runtime_s

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TwoPanelCandidateRecord:
        """Constructs record from serialized dictionary, ignoring unknown extra keys."""
        import dataclasses
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        if "total_panel_area_m2" in d and "total_panel_area" not in filtered:
            filtered["total_panel_area"] = d["total_panel_area_m2"]
        return cls(**filtered)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "iteration": self.iteration,
            "method": self.method,
            "params": self.params,
            "is_feasible": self.is_feasible,
            "total_panel_area_m2": float(self.total_panel_area),
            "rejection_reason": self.rejection_reason,
            "rejection_message": self.rejection_message,
            "rejection_details": self.rejection_details,
            "objective_value": float(self.objective_value) if (self.objective_value is not None and math.isfinite(self.objective_value)) else None,
            "metrics": self.metrics,
            "affected_cells_count": self.affected_cells_count,
            "recomputed_cells_count": self.recomputed_cells_count,
            "reused_cells_count": self.reused_cells_count,
            "total_active_cells": self.total_active_cells,
            "affected_rays_count": self.affected_rays_count,
            "recomputed_rays_count": self.recomputed_rays_count,
            "reused_rays_count": self.reused_rays_count,
            "overlap_cells_count": self.overlap_cells_count,
            "union_cells_count": self.union_cells_count,
            "gpu_kernel_time_ms": self.gpu_kernel_time_ms,
            "host_to_device_time_ms": self.host_to_device_time_ms,
            "device_to_host_time_ms": self.device_to_host_time_ms,
            "total_runtime_s": round(self.total_runtime_s, 4),
            "certificate_status": self.certificate_status,
            "certificate_violations": self.certificate_violations,
            "max_certificate_bound_k": self.max_certificate_bound_k,
            "max_observed_error_k": self.max_observed_error_k,
            "surrogate_predicted_objective": self.surrogate_predicted_objective,
            "surrogate_uncertainty": self.surrogate_uncertainty,
            "acquisition_strategy": self.acquisition_strategy,
        }


class TwoPanelCandidateLedger:
    """In-memory database and exporter for two-panel optimization history."""

    def __init__(self):
        self.records: List[TwoPanelCandidateRecord] = []

    def add(self, record: TwoPanelCandidateRecord):
        """Appends a candidate evaluation record."""
        self.records.append(record)

    def __len__(self) -> int:
        return len(self.records)

    def get_feasible(self) -> List[TwoPanelCandidateRecord]:
        """Returns all geographically and structurally feasible candidates."""
        return [r for r in self.records if r.is_feasible]

    def get_rejected(self) -> List[TwoPanelCandidateRecord]:
        """Returns all rejected candidates."""
        return [r for r in self.records if not r.is_feasible]

    def get_best(self) -> Optional[TwoPanelCandidateRecord]:
        """Returns the feasible candidate with the lowest objective value."""
        feasible = self.get_feasible()
        if not feasible:
            return None
        return min(feasible, key=lambda r: r.objective_value)

    def get_top_n(self, n: int = 5) -> List[TwoPanelCandidateRecord]:
        """Returns the top N feasible candidates ordered by objective improvement."""
        feasible = self.get_feasible()
        feasible_sorted = sorted(feasible, key=lambda r: r.objective_value)
        return feasible_sorted[:n]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes ledger to a Python dictionary."""
        return {
            "records": [r.to_dict() for r in self.records],
            "total_candidates": len(self.records),
            "feasible_candidates": len(self.get_feasible()),
            "rejected_candidates": len(self.get_rejected()),
        }

    def save_json(self, path: Path):
        """Serializes ledger to JSON file."""
        data = [r.to_dict() for r in self.records]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def save_csv(self, path: Path):
        """Serializes ledger to CSV table."""
        rows = []
        for r in self.records:
            p = r.params
            m = r.metrics or {}
            row = {
                "candidate_id": r.candidate_id,
                "iteration": r.iteration,
                "method": r.method,
                "is_feasible": r.is_feasible,
                "rejection_reason": r.rejection_reason or "",
                "total_panel_area_m2": r.total_panel_area,
                "objective_value": r.objective_value if math.isfinite(r.objective_value) else "",
                # Panel 1
                "x1": p.get("x1", ""),
                "y1": p.get("y1", ""),
                "length1": p.get("length1", ""),
                "width1": p.get("width1", ""),
                "height1": p.get("height1", ""),
                "heading1": p.get("heading_deg1", ""),
                "albedo1": p.get("albedo1", ""),
                "area1_m2": p.get("area1_m2", ""),
                # Panel 2
                "x2": p.get("x2", ""),
                "y2": p.get("y2", ""),
                "length2": p.get("length2", ""),
                "width2": p.get("width2", ""),
                "height2": p.get("height2", ""),
                "heading2": p.get("heading_deg2", ""),
                "albedo2": p.get("albedo2", ""),
                "area2_m2": p.get("area2_m2", ""),
                # Comfort metrics
                "mean_utci_c": m.get("mean_utci_c", ""),
                "p90_utci_c": m.get("p90_utci_c", ""),
                "max_utci_c": m.get("max_utci_c", ""),
                "mean_tmrt_c": m.get("mean_tmrt_c", ""),
                "delta_mean_utci_c": m.get("delta_mean_utci_c", ""),
                "thermal_improvement_utci_c": m.get("thermal_improvement_utci_c", ""),
                "peak_local_tmrt_improvement_k": m.get("peak_local_tmrt_improvement_k", ""),
                "pct_improved_cells": m.get("pct_improved_cells", ""),
                "pct_comfortable_cells": m.get("pct_comfortable_cells", ""),
                "estimated_construction_cost_usd": m.get("estimated_construction_cost_usd", ""),
                # Spatial reuse
                "affected_cells": r.affected_cells_count if r.affected_cells_count is not None else "",
                "recomputed_cells": r.recomputed_cells_count if r.recomputed_cells_count is not None else "",
                "reused_cells": r.reused_cells_count if r.reused_cells_count is not None else "",
                "overlap_cells": r.overlap_cells_count if r.overlap_cells_count is not None else "",
                "union_cells": r.union_cells_count if r.union_cells_count is not None else "",
                # Performance
                "gpu_kernel_time_ms": r.gpu_kernel_time_ms if r.gpu_kernel_time_ms is not None else "",
                "total_runtime_s": r.total_runtime_s,
                # Certification
                "certificate_status": r.certificate_status or "",
                "certificate_violations": r.certificate_violations if r.certificate_violations is not None else "",
                "max_certificate_bound_k": r.max_certificate_bound_k if r.max_certificate_bound_k is not None else "",
                # Surrogate
                "surrogate_pred_obj": r.surrogate_predicted_objective if r.surrogate_predicted_objective is not None else "",
                "surrogate_uncertainty": r.surrogate_uncertainty if r.surrogate_uncertainty is not None else "",
                "acquisition_strategy": r.acquisition_strategy or "",
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)

    def to_dataframe(self) -> pd.DataFrame:
        """Converts feasible candidates to a pandas DataFrame for analysis."""
        rows = [r.to_dict() for r in self.records]
        return pd.DataFrame(rows)
