# Stage 32: Tree-Aware Incremental Recomputation Limitations

**Status**: `STAGE_32_TREE_AWARE_INCREMENTAL_COMPLETE`  
**Classification**: `PROVISIONAL_TREE_GEOMETRY` / `NOT_FIELD_VALIDATED` / `SENSITIVITY_USE_ONLY`  

---

## Technical Constraints & Boundaries
1. Incremental invalidation bounds the spatial shadow envelope derived from tree height and solar elevation.
2. Cells outside the conservative bounding cone are reused directly with zero floating-point re-evaluation.
3. Speedup is proportional to the fraction of unaffected grid domain.
4. Tree geometry modifications tested here remain provisional Level 1 bounds; results do not represent field-measured canopy growth.
