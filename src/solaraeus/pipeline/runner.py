"""
Unified Runner for SOLARAEUS 5-Stage Microclimate Pipeline Architecture:

1. Data Ingestion: Vector GIS, heights, materials, terrain, mesh and grid generation.
2. Calculation: Baseline raytraced microclimate simulation (shadow, SVF, Tmrt, UTCI).
3. Intervention: Urban shade structures/trees, full recomputation, cooling deltas.
4. Incremental Solver: Certified spatial cone & horizon bounding, fast differential update.
5. AI Solver: Surrogate modeling & multi-objective optimization for optimal interventions.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from solaraeus.pipeline.config import PipelineConfig
from solaraeus.pipeline.stage1_data_ingestion import run_stage_data_ingestion
from solaraeus.pipeline.stage2_calculation import run_stage_calculation
from solaraeus.pipeline.stage3_intervention import run_stage_intervention
from solaraeus.pipeline.stage4_incremental_solver import run_stage_incremental_solver
from solaraeus.pipeline.stage5_ai_solver import run_stage_ai_solver


def run_pipeline(config: Optional[PipelineConfig] = None) -> Dict[str, Any]:
    """
    Executes the unified 5-stage SOLARAEUS pipeline in one run.

    Args:
        config: Optional pipeline configuration (defaults to Church Street).

    Returns:
        Manifest dictionary of execution status, timings, and results across all 5 stages.
    """
    if config is None:
        config = PipelineConfig()

    t_pipeline_start = time.perf_counter()
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Destination folder: config.output_dir (or timestamped subdirectory)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    if config.verbose:
        print("\n" + "=" * 80)
        print("          SOLARAEUS UNIFIED 5-STAGE MICROCLIMATE PIPELINE")
        print("=" * 80)
        print(f"Area Domain:       {config.area}")
        print(f"Input Data Folder: {config.data_dir}")
        print(f"Output Directory:  {config.output_dir}")
        print(f"Stages Selected:   {config.stages_to_run}")
        print(f"Execution Time:    {timestamp_utc} UTC")
        print("=" * 80)

    stage_summaries: Dict[str, Any] = {}
    scene = None
    grid_info = None
    baseline_result = None
    int_scene = None
    int_result = None
    cooling_deltas = None
    full_intervention_time_sec = None

    # Stage 1: Data Ingestion
    if 1 in config.stages_to_run:
        scene, grid_info, s1_summary = run_stage_data_ingestion(config)
        stage_summaries["01_data_ingestion"] = s1_summary

    # Stage 2: Calculation (Baseline)
    if 2 in config.stages_to_run:
        baseline_result, s2_summary = run_stage_calculation(config, scene=scene, grid_info=grid_info)
        stage_summaries["02_calculation"] = s2_summary

    # Stage 3: Intervention
    if 3 in config.stages_to_run:
        int_scene, int_result, cooling_deltas, s3_summary = run_stage_intervention(
            config, baseline_scene=scene, baseline_result=baseline_result
        )
        stage_summaries["03_intervention"] = s3_summary
        full_intervention_time_sec = s3_summary.get("wall_time_sec")

    # Stage 4: Incremental Solver
    if 4 in config.stages_to_run:
        inc_result, speedup_metrics, s4_summary = run_stage_incremental_solver(
            config,
            baseline_scene=scene,
            intervention_scene=int_scene,
            baseline_result=baseline_result,
            full_intervention_time_sec=full_intervention_time_sec,
        )
        stage_summaries["04_incremental_solver"] = s4_summary

    # Stage 5: AI Solver
    if 5 in config.stages_to_run:
        best_cand, pareto_set, s5_summary = run_stage_ai_solver(
            config, baseline_scene=scene, baseline_result=baseline_result
        )
        stage_summaries["05_ai_solver"] = s5_summary

    total_wall_time_sec = time.perf_counter() - t_pipeline_start

    # Build master manifest
    manifest: Dict[str, Any] = {
        "pipeline_status": "COMPLETED_SUCCESSFULLY",
        "area": config.area,
        "execution_timestamp_utc": timestamp_utc,
        "total_wall_time_sec": round(total_wall_time_sec, 3),
        "data_directory": str(config.data_dir),
        "output_directory": str(config.output_dir),
        "stages_executed": [f"stage_{s}" for s in config.stages_to_run],
        "stages": stage_summaries,
    }

    manifest_file = config.output_dir / "pipeline_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Write Markdown Executive Summary Report
    report_lines = [
        f"# SOLARAEUS Microclimate Pipeline Execution Report",
        f"",
        f"- **Area**: `{config.area}`",
        f"- **Timestamp (UTC)**: `{timestamp_utc}`",
        f"- **Total Runtime**: `{total_wall_time_sec:.2f} seconds`",
        f"- **Output Directory**: `{config.output_dir}`",
        f"",
        f"---",
        f"",
        f"## 1. Stage Summaries",
        f"",
    ]
    for sname, sdata in stage_summaries.items():
        report_lines.append(f"### Stage {sname.replace('_', ' ').title()}")
        report_lines.append(f"- Status: `{sdata.get('status', 'OK')}`")
        if "wall_time_sec" in sdata:
            report_lines.append(f"- Runtime: `{sdata['wall_time_sec']} s`")
        if sname == "02_calculation" and "metrics" in sdata:
            m = sdata["metrics"]
            report_lines.append(f"- Baseline Mean Tmrt: `{m['tmrt_mean_c']:.2f} °C`")
            report_lines.append(f"- Baseline Mean UTCI: `{m['utci_mean_c']:.2f} °C`")
        elif sname == "03_intervention" and "cooling_deltas" in sdata:
            cd = sdata["cooling_deltas"]
            report_lines.append(f"- Max Tmrt Cooling: `-{cd['max_tmrt_cooling_k']:.2f} K`")
            report_lines.append(f"- Max UTCI Cooling: `-{cd['max_utci_cooling_k']:.2f} K`")
        elif sname == "04_incremental_solver" and "speedup" in sdata:
            sp = sdata["speedup"]
            report_lines.append(f"- Incremental Speedup: `{sp['speedup_factor']}x`")
            report_lines.append(f"- Cell Recomputation Workload Reduction: `{sp['workload_reduction_percentage']}%`")
        elif sname == "05_ai_solver":
            report_lines.append(f"- Optimal Design ID: `{sdata.get('optimal_candidate_id', 'N/A')}`")
            report_lines.append(f"- Total Candidate Evaluations: `{sdata.get('total_evaluations', 0)}`")
        report_lines.append("")

    report_file = config.output_dir / "pipeline_report.md"
    report_file.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    if config.verbose:
        print("\n" + "=" * 80)
        print(f"PIPELINE RUN COMPLETED in {total_wall_time_sec:.2f} seconds!")
        print(f"Master Manifest: {manifest_file}")
        print(f"Report:          {report_file}")
        print("=" * 80 + "\n")

    return manifest
