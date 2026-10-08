# Stage 31: GPU Tree-Shadow Backend Limitations

**Status**: `STAGE_31_GPU_TREE_SHADOW_COMPLETE`  
**Classification**: `PROVISIONAL_TREE_GEOMETRY` / `NOT_FIELD_VALIDATED` / `SENSITIVITY_USE_ONLY`  

---

## Technical Constraints & Boundaries
1. The GPU tree-shadow backend compiles a high-performance CUDA kernel for direct tree-ray intersection.
2. Bit-exact shadow mask equivalence with the CPU reference solver is confirmed across isolated, multi-tree, and terrain-coupled configurations.
3. Tree geometry remains provisional photo-estimated Level 1 representations.
4. Optical canopy physics (LAI/transmissivity) are uncalibrated and intended solely for sensitivity analysis.
