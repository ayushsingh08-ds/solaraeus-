"""
FastAPI Server for SOLARAEUS Interactive Digital Twin Engine.

Provides REST APIs for:
- Discovering case study areas in data/input/
- Processing case area data with user timestamp into data/processed/<area>/<timestamp>/
- Optimizing multi-canopy shade placements into data/optimized/<area>/<timestamp>/
- Serving interactive 3D WebGL interface and spatial microclimate datasets.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from solaraeus.pipeline.engine import (
    get_available_case_areas,
    process_case_data,
    optimize_canopies,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
STATIC_DIR = ROOT_DIR / "simulation_3d"

app = FastAPI(
    title="SOLARAEUS Urban Microclimate Engine",
    description="Interactive digital twin for certified microclimate simulation and optimal canopy placement",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProcessRequest(BaseModel):
    area: str = "church_street"
    timestamp: Optional[str] = None
    grid_resolution_m: float = 2.0
    use_gpu: bool = False


class OptimizeRequest(BaseModel):
    area: str = "church_street"
    timestamp: Optional[str] = None
    num_shades: int = 3
    canopy_width_m: float = 4.0
    canopy_length_m: float = 8.0
    canopy_height_m: float = 4.0
    transmissivity: float = 0.10
    optimization_strategy: str = "max_pedestrian_cooling"


@app.get("/api/areas")
def list_areas():
    """Lists all available input case study areas from data/input/."""
    areas = get_available_case_areas()
    return {"areas": areas}


@app.get("/api/runs")
def list_runs(area: str = "church_street"):
    """Lists existing processed and optimized runs for an area."""
    proc_dir = ROOT_DIR / "data" / "processed" / area
    opt_dir = ROOT_DIR / "data" / "optimized" / area
    
    processed_runs = []
    if proc_dir.exists():
        for d in sorted(proc_dir.iterdir(), reverse=True):
            if d.is_dir():
                s_file = d / "processing_summary.json"
                meta = {}
                if s_file.exists():
                    try:
                        meta = json.loads(s_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                processed_runs.append({
                    "timestamp": d.name,
                    "summary": meta,
                })

    optimized_runs = []
    if opt_dir.exists():
        for d in sorted(opt_dir.iterdir(), reverse=True):
            if d.is_dir():
                c_file = d / "cooling_delta.json"
                can_file = d / "optimal_canopies.json"
                meta = {}
                canopies = []
                if c_file.exists():
                    try:
                        meta = json.loads(c_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                if can_file.exists():
                    try:
                        canopies = json.loads(can_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                optimized_runs.append({
                    "timestamp": d.name,
                    "summary": meta,
                    "num_canopies": len(canopies),
                })

    return {
        "area": area,
        "processed_runs": processed_runs,
        "optimized_runs": optimized_runs,
    }


@app.post("/api/process")
def api_process(req: ProcessRequest):
    """Processes input case data and writes to data/processed/<area>/<timestamp>/."""
    ts = req.timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        summary = process_case_data(
            area=req.area,
            timestamp=ts,
            grid_resolution_m=req.grid_resolution_m,
            use_gpu=req.use_gpu,
        )
        return {
            "status": "SUCCESS",
            "message": f"Case data for '{req.area}' processed successfully with timestamp '{ts}'.",
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimize")
def api_optimize(req: OptimizeRequest):
    """Calculates best canopy positions across the map and writes to data/optimized/<area>/<timestamp>/."""
    try:
        res = optimize_canopies(
            area=req.area,
            timestamp=req.timestamp,
            num_shades=req.num_shades,
            canopy_width=req.canopy_width_m,
            canopy_length=req.canopy_length_m,
            canopy_height=req.canopy_height_m,
            transmissivity=req.transmissivity,
            optimization_strategy=req.optimization_strategy,
        )
        return {
            "status": "SUCCESS",
            "message": f"Optimized placement for {len(res['canopies'])} canopies calculated successfully.",
            "data": res,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/{area}/{timestamp}")
def get_case_data(area: str, timestamp: str):
    """
    Returns unified 3-layer data for 3D visualization:
    1. Baseline microclimate (Tmrt, UTCI, shadows, mesh)
    2. Optimal canopy placement (canopy models, coordinates)
    3. Cooling delta (Tmrt reduction, UTCI reduction, statistics)
    """
    import numpy as np

    proc_dir = ROOT_DIR / "data" / "processed" / area / timestamp
    opt_dir = ROOT_DIR / "data" / "optimized" / area / timestamp

    if not proc_dir.exists():
        raise HTTPException(status_code=404, detail=f"Processed run '{timestamp}' not found for area '{area}'")

    # Load Stage 1 Scene Mesh
    scene_file = proc_dir / "01_data_ingestion" / "scene_mesh.json"
    grid_file = proc_dir / "01_data_ingestion" / "pedestrian_grid.json"
    
    scene_data = json.loads(scene_file.read_text(encoding="utf-8")) if scene_file.exists() else {}
    grid_info = json.loads(grid_file.read_text(encoding="utf-8")) if grid_file.exists() else {}

    # Load Baseline Calculation
    calc_dir = proc_dir / "02_calculation"
    b_shadow = np.load(calc_dir / "baseline_shadow.npz")["shadow_mask"].tolist() if (calc_dir / "baseline_shadow.npz").exists() else []
    b_tmrt = np.load(calc_dir / "baseline_tmrt.npz")["tmrt"].tolist() if (calc_dir / "baseline_tmrt.npz").exists() else []
    b_utci = np.load(calc_dir / "baseline_utci.npz")["utci"].tolist() if (calc_dir / "baseline_utci.npz").exists() else []
    
    summary_file = proc_dir / "processing_summary.json"
    proc_summary = json.loads(summary_file.read_text(encoding="utf-8")) if summary_file.exists() else {}

    # Load Optimization data if available
    canopies = []
    canopy_meshes = []
    opt_summary = {}
    opt_tmrt = []
    opt_utci = []
    delta_tmrt = []

    if opt_dir.exists():
        if (opt_dir / "optimal_canopies.json").exists():
            canopies = json.loads((opt_dir / "optimal_canopies.json").read_text(encoding="utf-8"))
        if (opt_dir / "intervention_mesh.json").exists():
            canopy_meshes = json.loads((opt_dir / "intervention_mesh.json").read_text(encoding="utf-8"))
        if (opt_dir / "cooling_delta.json").exists():
            opt_summary = json.loads((opt_dir / "cooling_delta.json").read_text(encoding="utf-8"))
        if (opt_dir / "optimized_tmrt.npz").exists():
            opt_tmrt = np.load(opt_dir / "optimized_tmrt.npz")["tmrt"].tolist()
        if (opt_dir / "optimized_utci.npz").exists():
            opt_utci = np.load(opt_dir / "optimized_utci.npz")["utci"].tolist()
        if (opt_dir / "cooling_delta_tmrt.npz").exists():
            delta_tmrt = np.load(opt_dir / "cooling_delta_tmrt.npz")["delta_tmrt_k"].tolist()

    return {
        "area": area,
        "timestamp": timestamp,
        "grid": grid_info,
        "scene_mesh": scene_data,
        "data1_baseline": {
            "summary": proc_summary,
            "shadow_mask": b_shadow,
            "tmrt": b_tmrt,
            "utci": b_utci,
        },
        "data2_canopies": {
            "canopies": canopies,
            "meshes": canopy_meshes,
        },
        "data3_cooling": {
            "summary": opt_summary,
            "optimized_tmrt": opt_tmrt,
            "optimized_utci": opt_utci,
            "delta_tmrt_k": delta_tmrt,
        },
    }


# Mount static assets
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Runs the FastAPI server with uvicorn."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
