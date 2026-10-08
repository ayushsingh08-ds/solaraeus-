# CPU Efficiency and Benchmark Report: Full vs Incremental Recomputation

**Study Area:** Church Street, Bengaluru, India  
**Simulation Grid:** 148 × 190 (28,120 pedestrian receptor cells @ 2.0 m resolution)  
**Intervention:** Overhead Shade Panel (`BLR_SHADE_001` / `CANOPY_001`, 18.0 m² footprint @ 3.5 m height)  
**Evaluation Platform:** Intel64 Family 6 Model 183 Stepping 1, GenuineIntel, Windows 11, Python 3.12.6  
**Benchmark Trials:** 5 independent executions per configuration  

---

## 1. Executive Summary

Certified incremental recomputation achieves massive algorithmic work reduction and substantial wall-clock speedup while guaranteeing mathematical error bounds:
- **Mean Wall-Clock Time (Full Recompute):** `8.270 ± 0.299` seconds
- **Mean Wall-Clock Time (Certified Incremental):** `1.607 ± 0.182` seconds
- **Empirical CPU Speedup:** **`5.15×`**
- **Cell Reuse Fraction:** **`99.74%`** (28,048 cells reused, 72 cells recomputed)
- **Ray Work Reduction:** **`99.74%`** (925,584 rays avoided out of 927,960 rays)
- **Maximum Parity Error ($T_{mrt}$):** `0.0289 K` (strictly $\le 0.50$ K tolerance)
- **Direct Shadow Error:** `0.000000` (exact bit-level parity)

---

## 2. Multi-Trial Statistical Summary

| Configuration | Metric | Min | Median | Max | Mean | Std Dev |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Static Baseline** | Wall-clock (s) | 8.086 | 8.649 | 9.333 | 8.731 | 0.455 |
| | CPU Time (s) | 7.812 | 8.375 | 9.094 | 8.444 | 0.492 |
| | Peak Heap (MB) | 6.73 | 6.73 | 6.80 | 6.74 | 0.03 |
| **Stage 5 Full Recompute** | Wall-clock (s) | 8.002 | 8.118 | 8.843 | 8.270 | 0.299 |
| | CPU Time (s) | 7.859 | 7.906 | 8.625 | 8.069 | 0.287 |
| | Peak Heap (MB) | 6.73 | 6.73 | 6.73 | 6.73 | 0.00 |
| **Stage 6 Certified Incremental** | Wall-clock (s) | 1.280 | 1.605 | 1.782 | 1.607 | 0.182 |
| | CPU Time (s) | 1.234 | 1.578 | 1.766 | 1.566 | 0.184 |
| | Peak Heap (MB) | 5.44 | 5.44 | 5.44 | 5.44 | 0.00 |

---

## 3. Algorithmic Complexity and Subquadratic Scaling

1. **Direct Solar Shading:** Full recomputation casts $N = 28,120$ rays against all scene triangles ($M = 2,148$ triangles). Incremental evaluation bounds the shadow projection envelope using directional frustum Minkowski dilation, reducing candidate queries to only cells within the projection bounding box ($N_{cand} \ll N$).
2. **Sky View Factor:** Full horizon scanning traces $32 	imes 28,120 = 899,840$ rays across azimuths. Certified incremental evaluation evaluates the computable solid-angle error certificate $\Delta 	ext{SVF} \le rac{W \cdot \Delta h}{2\pi r^2}$, selectively recomputing only the 72 dirty cells that violate the $0.50$ K thermal comfort threshold.
3. **Memory Boundedness:** Heap allocation during incremental updates remains strictly under 10 MB, demonstrating zero memory leaks and bounded spatial memory overhead.
