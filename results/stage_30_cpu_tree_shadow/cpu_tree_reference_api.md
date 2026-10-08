# SOLARAEUS CPU Tree-Shadow Reference Solver API

**API Version**: `2.2.0-cpu-tree`  
**Status**: `STAGE_30_CPU_TREE_SHADOW_REFERENCE_COMPLETE`  
**Data Classification**: `PROVISIONAL_TREE_GEOMETRY` / `NOT_FIELD_VALIDATED` / `SENSITIVITY_USE_ONLY`  

---

## Capabilities & Architecture
- Evaluates Level 1 analytical tree geometry:
  - Trunk: vertical cylinder $x^2 + y^2 \le r^2, z \in [z_{ground}, z_{crown\_base}]$
  - Crown: 3D ellipsoid $\frac{(x-x_0)^2}{r_x^2} + \frac{(y-y_0)^2}{r_y^2} + \frac{(z-z_c)^2}{r_z^2} \le 1$
- Preserves exact 100% backward parity with `2.1.0-cpu-terrain` and `2.0.0-cpu-ref` when trees are absent.
- Interacts with synthetic terrain elevation: rays originate at $z(x, y) + h_{ped}$.
