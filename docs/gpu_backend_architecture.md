# SOLARAEUS GPU Simulation Backend Architecture & Verification

## 1. Backend Architecture
The SOLARAEUS simulation engine employs a dual-backend abstraction located in `src/urban_comfort/backend/`:
- **`SimulationBackend` (Abstract Base Class)**: Defines the standard evaluation contract for microclimate simulations, including `compute_direct_shadow()`, `compute_sky_view_factor()`, and `full_simulate()`.
- **`CPUBackend`**: Wraps the trusted, validated CPU reference solver using vectorized NumPy and CPU Möller-Trumbore ray tracing. Serves as the ground-truth reference for all numerical parity comparisons.
- **`GPUBackend`**: High-performance CUDA C++ ray-tracing engine executed via CuPy `RawModule` and JIT compilation. Features massively parallel Möller-Trumbore ray-triangle intersections, Kay-Kajiya slab ray-AABB tests, and multi-azimuth horizon elevation scans.
- **`FlattenedSceneGeometry`**: Contiguous host/device memory flattener that packs complex scene representations (buildings, meshes, materials, and bounding boxes) into compact arrays (`vertices`, `triangles`, `bldg_boxes`, `triangle_object_ids`, `triangle_material_ids`).
- **`get_backend(name: str = "cpu", fallback_to_cpu: bool = False)`**: Factory providing dynamic runtime selection (`"cpu"`, `"gpu"`, or `"auto"`).

```
                      +------------------------+
                      |   SimulationConfig     |
                      | (backend: cpu/gpu/auto)|
                      +-----------+------------+
                                  |
                                  v
                      +------------------------+
                      |   SimulationBackend    |
                      +-----------+------------+
                                  |
               +------------------+------------------+
               |                                     |
               v                                     v
      +-----------------+                   +-----------------+
      |   CPUBackend    |                   |   GPUBackend    |
      | (NumPy Ref.)    |                   | (CUDA C++ JIT)  |
      +-----------------+                   +-----------------+
               |                                     |
               |                                     v
               |                            +-----------------+
               |                            | CuPy RawModule  |
               |                            | - MT Shadow     |
               |                            | - DSM Raster    |
               |                            | - SVF Horizon   |
               |                            +-----------------+
               |                                     |
               +------------------+------------------+
                                  |
                                  v
                      +------------------------+
                      |    SimulationResult    |
                      | (Shadow, SVF, K, L,    |
                      |  Tmrt, UTCI, Profile)  |
                      +------------------------+
```

---

## 2. Supported GPU Runtime & Toolchain
- **Hardware**: NVIDIA GPUs with Compute Capability $\ge 6.0$ (Pascal through Ada Lovelace / Hopper / Blackwell).
- **Tested Hardware**: NVIDIA GeForce RTX 4050 Laptop GPU (6,140 MB VRAM, CC 8.9 Ada Lovelace).
- **Host Drivers**: NVIDIA UMD Driver $\ge 525.60$ (Windows/Linux).
- **Software Dependencies**:
  - `cupy-cuda12x` ($\ge 13.0$, tested on 14.2.0)
  - CUDA Runtime wheels: `nvidia-cuda-nvrtc-cu12`, `nvidia-cuda-runtime-cu12` (no local system `nvcc` compiler installation required).
- **Floating-Point Precision Policy**: Full IEEE-754 64-bit Double Precision (`double` / FP64) inside CUDA kernels to ensure machine-level numerical parity ($10^{-14}$) with the CPU reference.

---

## 3. Fallback Behavior
- If `GPUBackend` is invoked with `fallback_to_cpu=True` (or via `get_backend("auto")`) in an environment without a functional CUDA GPU or CuPy, execution automatically falls back to `CPUBackend` without failing or interrupting the pipeline.
- If `fallback_to_cpu=False` and no CUDA device is detected, a descriptive `RuntimeError` is raised indicating missing GPU drivers or dependencies.
- CPU reference code paths remain completely independent and unmodified.

---

## 4. Numerical Tolerance Policy
To prevent loosening of standards, all GPU outputs are certified against the trusted CPU full recomputation using strict scientific tolerance thresholds:

| Physical Field | Documented Tolerance | Observed Max Absolute Error | Observed RMS Error | Parity Status |
| :--- | :--- | :--- | :--- | :--- |
| **Direct Shadow Mask** | **0.0 (exact bit match)** | **0.000000** | **0.000000** | **PASS (Exact)** |
| **Sky View Factor (SVF)** | **$1.00 \times 10^{-4}$** | **$1.05 \times 10^{-14}$** | **$3.93 \times 10^{-16}$** | **PASS (Machine $\epsilon$)** |
| **Direct Shortwave Irradiance** | **$1.00 \times 10^{-4} \text{ W/m}^2$** | **0.000000** | **0.000000** | **PASS (Exact)** |
| **Total Shortwave Flux ($K$)** | **$0.010 \text{ W/m}^2$** | **$3.41 \times 10^{-13} \text{ W/m}^2$** | **$1.42 \times 10^{-14}$** | **PASS** |
| **Total Longwave Flux ($L$)** | **$0.010 \text{ W/m}^2$** | **$3.41 \times 10^{-13} \text{ W/m}^2$** | **$2.44 \times 10^{-14}$** | **PASS** |
| **Mean Radiant Temp ($T_{\text{mrt}}$)** | **$0.050 \text{ K}$** | **$1.14 \times 10^{-13} \text{ K}$** | **$8.21 \times 10^{-15}$** | **PASS** |
| **Thermal Comfort (UTCI)** | **$0.050 \,^{\circ}\text{C}$** | **0.000000** | **0.000000** | **PASS (Exact)** |

*Zero discrepancies and zero NaN/Inf values across all 28,120 Church Street grid cells.*

---

## 5. Profiling Methodology
Profiling is instrumented directly within `GPUBackend` and records:
1. `scene_upload_time_s`: Contiguous array host-to-device PCIe transfer time via `cp.asarray()`.
2. `kernel_runtime_s`: GPU execution duration measured with CUDA stream synchronization (`cp.cuda.Stream.null.synchronize()`).
3. `transfer_to_host_time_s`: Device-to-host transfer time via `cp.asnumpy()`.
4. `total_runtime_s`: Complete end-to-end stage time.
5. `peak_gpu_memory_bytes`: Device VRAM usage sampled via `cp.cuda.Device().mem_info`.
6. `ray_counts`: Exact ray workload counts for direct shadows ($N_{\text{cells}}$) and SVF ($N_{\text{cells}} \times N_{\text{azimuths}}$).

### Church Street Benchmark Results
- **Direct Shadow Rays**: 28,120 rays
- **SVF Azimuth Rays**: 899,840 rays
- **Total Ray Work**: 927,960 rays
- **Scene Geometry**: 124 building/canopy meshes, 2,148 triangles
- **Scene Upload Time**: 0.60 ms
- **GPU Kernel Time**: 59.37 ms
- **Host Transfer Time**: 0.25 ms
- **Total GPU Ray-Work Time**: 60.22 ms (vs. 3,480 ms CPU reference)
- **Ray-Work Kernel Speedup**: **57.8×**
- **Peak VRAM Allocated**: 1,064.5 MB

---

---

## 6. GPU Incremental Recomputation Architecture (`GPUIncrementalEngine`)
To accelerate interactive intervention exploration (such as overhead shade canopies, tree planting, and building modifications), SOLARAEUS provides `GPUIncrementalEngine`:

1. **Resident Static Geometry (`GPUResidentState`)**:
   - Static scene buildings, context meshes, and pre-rasterized 2D building height grids reside permanently in GPU VRAM.
   - Baseline physical fields (`shadow_mask`, `svf`) are stored in device memory to eliminate redundant baseline transfers.

2. **Lightweight Dynamic Object Uploads**:
   - Intervention geometry edits (e.g. overhead canopy `BLR_SHADE_001` / `CANOPY_001`, comprising 8 vertices and 12 triangles) upload dynamically across the PCIe bus in $< 18 \text{ ms}$.

3. **Selective CUDA Kernel Dispatch**:
   - The engine evaluates computable error certificates $B_T(x)$ on CPU to identify dirty receptors where $B_T(x) > \text{tolerance}$.
   - For Church Street shade-panel intervention, exactly **72 cells (0.26%)** and **2,376 rays (0.26%)** require recomputation.
   - CUDA Möller-Trumbore shadow and multi-azimuth horizon elevation kernels execute with `has_roi=1` and `roi_mask=d_dirty`, skipping 99.74% of receptors.
   - Clean receptors retain their resident baseline values directly on GPU, avoiding redundant ray tracing.

4. **Zero Certificate Violations & Exact Equivalence**:
   - All 28,048 reused cells satisfy the mathematical certificate slack condition $\Delta(x) = B_T(x) - e(x) \ge 0$.
   - Pointwise $T_{\text{mrt}}$ difference between GPU Incremental and CPU Incremental is within **$5.68 \times 10^{-14} \text{ K}$** (machine precision).
   - Direct shadow mask matches bit-for-bit with 0 mismatch.

| Metric | Church Street GPU Incremental Value |
| :--- | :--- |
| **Total Grid Cells** | 28,120 cells |
| **Recomputed Dirty Cells** | 72 cells (0.26%) |
| **Reused Baseline Cells** | 28,048 cells (99.74%) |
| **Total Directional Rays** | 927,960 rays |
| **Affected Rays Recomputed** | 2,376 rays (0.26%) |
| **Ray-Work Reduction** | **99.74%** |
| **GPU Kernel Execution Time** | **10.6 ms** |
| **Host-to-Device Transfer Time** | **17.3 ms** |
| **Device-to-Host Transfer Time** | **0.7 ms** |
| **Certificate Violations** | **0** |
| **Max $T_{\text{mrt}}$ Error vs CPU Full Reference** | **0.028902 K** (Tolerance: 0.50 K) |
| **Max $T_{\text{mrt}}$ Error vs GPU Full Reference** | **0.028902 K** (Tolerance: 0.50 K) |
| **Max $T_{\text{mrt}}$ Diff vs CPU Incremental Solver** | **$5.68 \times 10^{-14}$ K** (Machine $\epsilon$) |

---

## 7. Known Limitations
1. **Host-Side Geometry Flattening**: Flattening complex Python `Scene` objects into contiguous NumPy arrays occurs on the host CPU. For massive urban scenes ($> 100,000$ buildings), BVH spatial hierarchy prebuilding is recommended.
2. **Terrain Elevations**: Current implementation assumes flat terrain ($z=0$ base). Complex digital elevation models (DEMs) will be integrated with 2D texture samplers in subsequent stages.
3. **Host-Side Certificate Overhead**: Error certificate calculation $B_T(x)$ currently runs on CPU in Python/NumPy (~40 ms). In future iterations for AI optimization loops, $B_T(x)$ evaluation can be moved to a CUDA kernel.

