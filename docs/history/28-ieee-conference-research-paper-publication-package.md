## 28. IEEE Conference Research Paper Publication Package

### 28.1 Manuscript (`research_paper_sol/solaraeus.tex`)
- **Format**: IEEE 2-column conference style (`IEEEtran`).
- **Core Sections**:
  1. Introduction: Multi-paragraph problem formulation, state-of-the-art comparison (SOLWEIG, ENVI-met), identified operational gaps, and research objectives.
  2. Literature Review: Outdoor thermal comfort, SVF raymarching, WebGL digital twins, and incremental environmental simulation.
  3. Description of Data: High-fidelity LiDAR DEMs, Overture building footprints, and hourly ERA5 reanalysis meteorology.
  4. Methodology: Coordinate harmonization, DSM extrusion, Steyn 36-radial SVF, directional shadow tracing, Stefan-Boltzmann 6-flux $T_{\mathrm{mrt}}$ inversion, and pythermalcomfort UTCI.
  5. Results & Discussion: Washington Square Park empirical contrast ($14.7^\circ\mathrm{C}$ radiant relief) and Church Street intervention sensitivity.
  6. Structured Roadmap & Conclusion: Multi-day diurnal cycles, canopy attenuation, surrogate optimization, and dependency-aware incremental updates.
- **Verification**: Balanced environments (22 `\begin` / 22 `\end` matching pairs) and 23 complete citations with 0 unresolved keys.

### 28.2 Publication Diagrams & TikZ Source
- **Figure 1 (`fig1_architecture.png` & `fig1_architecture.tex`)**: 300 DPI system architecture and component taxonomy diagram (Inputs -> Preprocessing -> Physics -> Contracts -> Frontend).
- **Figure 2 (`fig2_methodology.png`, `fig2_dataflow.tex`, & `fig2_methodology.tex`)**: 300 DPI end-to-end dataflow pipeline with zero-crossing orthogonal routing and standard flowchart semantics.

---

