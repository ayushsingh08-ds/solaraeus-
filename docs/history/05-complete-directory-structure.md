## 5. Complete Directory Structure

```text
solaraeus/
├── .gitignore                                 # Clean exclusion of secrets, caches, and binaries
├── README.md                                  # Publication-grade technical documentation
├── configs/
│   └── baseline_scene.json                    # Canonical baseline scene configuration
├── examples/
│   ├── compare_full_incremental.py            # Baseline comparative benchmark script
│   ├── run_all_evaluations.py                 # Master automated research evaluation driver
│   ├── run_independent_audit.py               # Master independent scientific audit & mutation driver
│   ├── run_publication_validation.py          # Master publication validation and multi-trial suite
│   └── single_building.py                     # Single-building reference simulation example
├── researchpaper/                             # 17 reference literature PDFs on urban microclimate
├── results/                                   # Benchmark evaluation artifacts & publication outputs
│   ├── independent_audit_20261006_033239/     # Comprehensive independent scientific audit archive
│   │   ├── independent_certificate_audit.csv  # Decoupled error & slack audit (11 scenarios, 185k cells)
│   │   ├── dependency_coverage_audit.csv      # Complete 10-variable input-to-output trace matrix
│   │   ├── mutation_test_results.csv          # Sensitivity audit across 4 structural perturbations
│   │   ├── timing_audit.csv                   # Multi-trial N=5 timing audit across isolated phases
│   │   ├── repeated_edit_audit.csv            # Sequential edit audit & 0.0000K baseline reversion
│   │   ├── analytical_reference_audit.csv     # Independent closed-form analytical benchmarks
│   │   ├── reproducibility_audit.json         # Automated test suite verification & environment
│   │   ├── claim_audit.json                   # Scientific claim audit & defensibility documentation
│   │   ├── summary_metrics.json               # Aggregated audit metrics & overall verdict
│   │   └── plots/                             # 8 independent audit publication-grade figures
│   ├── publication_validation_20261004_224305/ # Publication validation archive
│   │   ├── reproducibility_results.csv        # Multi-trial N=5 statistics (mean, median, CI95)
│   │   ├── timing_breakdown.csv               # Granular wall-clock timing telemetry
│   │   ├── scaling_results.csv                # Domain scaling results (80m, 160m, 320m)
│   │   ├── edit_type_results.csv              # 10 canonical edit types
│   │   ├── tolerance_results.csv              # Error tolerance sweep (0.1K to 2.0K)
│   │   ├── certificate_tightness.csv          # Cell-by-cell slack and ratio percentiles
│   │   ├── repeated_edit_results.csv          # 5-step sequential edit evaluation
│   │   ├── baseline_comparison.csv            # Non-certified dirty box vs certified comparison
│   │   ├── analytical_reference_results.csv   # 4 independent analytical tests
│   │   ├── external_reference_results.csv     # UMEP/SOLWEIG compatibility matrix
│   │   ├── physics_audit.json                 # 17-item physics audit
│   │   ├── summary_metrics.json               # Aggregated telemetry summary
│   │   └── plots/                             # 9 publication-grade figures
│   │       ├── runtime_breakdown.png          # Stacked overhead vs compute phase breakdown
│   │       ├── speedup_vs_scene_size.png      # Scaling speedup curve (N=5 medians + CI)
│   │       ├── speedup_vs_tolerance.png       # Speedup vs error tolerance
│   │       ├── reused_cells_vs_tolerance.png  # Reused cell count vs tolerance
│   │       ├── actual_vs_predicted_error.png  # Error parity scatter confirming e <= B_T
│   │       ├── certificate_slack_distribution.png # Distribution of bound conservatism
│   │       ├── bound_to_error_ratio.png       # Bound-to-error ratio percentiles
│   │       ├── repeated_edit_error.png        # Sequence error & zero baseline drift
│   │       └── density_scaling.png            # Runtime scaling across building densities
│   ├── audit_report.json                      # 20-item physics & UMEP compatibility audit
│   ├── certificate_results.csv                # Detailed certificate audit metrics across runs
│   ├── edit_type_results.csv                  # Benchmark metrics across 5 edit categories
│   ├── independent_reference_results.csv      # Analytical benchmark verification results
│   ├── scaling_results.csv                    # Domain scaling telemetry (80m, 160m, 320m)
│   ├── summary_metrics.json                   # Aggregated campaign metrics & scientific status
│   └── eval_20261004_215818/                  # Timestamped archive of evaluation run
├── scripts/
│   └── run_first_milestone.py                 # Legacy milestone experiment script
├── src/
│   └── urban_comfort/                         # Production research prototype package
│       ├── __init__.py
│       ├── config.py                          # Data classes for Materials, Weather, SimulationConfig
│       ├── benchmark/                         # Evaluation & benchmarking framework
│       │   ├── __init__.py
│       │   ├── baseline_comparison.py         # Non-certified dirty box vs certified harness
│       │   ├── harness.py                     # Multi-trial statistical benchmarking engine
│       │   ├── independent_audit.py           # Decoupled certificate recalculation & mutation engine
│       │   ├── independent_reference.py       # Analytical benchmark verification functions
│       │   ├── repeated_edits.py              # Sequential edit evaluation module
│       │   ├── scenes.py                      # Parametric scaling & density scene generators
│       │   └── tightness.py                   # Certificate slack & ratio percentile analyzer
│       ├── comfort/
│       │   ├── __init__.py
│       │   └── utci.py                        # Vectorized UTCI polynomial & stress categories
│       ├── geometry/
│       │   ├── __init__.py
│       │   ├── primitives.py                  # BoundingBox2D, Building, GroundPlane
│       │   └── scene.py                       # Scene container & synthetic generators
│       ├── grid/
│       │   ├── __init__.py
│       │   └── pedestrian_grid.py             # Discrete 2D pedestrian grid mappings
│       ├── incremental/
│       │   ├── __init__.py
│       │   ├── affected_region.py             # Minkowski shadow plume candidate region & padding
│       │   ├── cache.py                       # SHA-256 state hashing & simulation cache
│       │   ├── certificate.py                 # Computable error certificate engine & verification
│       │   ├── dependency_graph.py            # DAG reachability and selective invalidation
│       │   └── update.py                      # Geometric edits, exact update, and certified update
│       ├── radiation/
│       │   ├── __init__.py
│       │   ├── longwave.py                    # Sky, wall, and ground longwave fluxes
│       │   ├── shortwave.py                   # 6-directional shortwave radiation fluxes
│       │   └── tmrt.py                        # Stefan-Boltzmann inversion and Tmrt calculation
│       ├── reference/
│       │   ├── __init__.py
│       │   └── full_recompute.py              # Ground-truth reference recomputation pipeline
│       ├── solar/
│       │   ├── __init__.py
│       │   └── solar_position.py              # NOAA astronomical solar position calculation
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── comparisons.py                 # Pointwise array comparison and error statistics
│       │   └── metrics.py                     # Shadow IoU, UTCI agreement, percentiles
│       └── visibility/
│           ├── __init__.py
│           ├── directional_visibility.py      # Multi-azimuth horizon search for Sky View Factor
│           ├── ray_intersection.py            # Vectorized Kay-Kajiya slab ray-AABB intersections
│           └── shadow.py                      # Direct beam solar shadow mask calculation
└── tests/                                     # 94 automated tests (unit, integration, adversarial)
    ├── test_adversarial_cases.py              # 8 original adversarial stress test cases
    ├── test_adversarial_suite.py              # Parameterized adversarial test suite
    ├── test_affected_region.py                # Shadow plume projection and fallback tests
    ├── test_cache_and_dependencies.py         # Cache hashing and DAG reachability tests
    ├── test_certificate_soundness.py          # Certificate bounds empirical verification
    ├── test_error_bounds.py                   # Mathematical soundness unit tests
    ├── test_extended_adversarial.py           # 12 extended adversarial stress scenarios
    ├── test_full_recompute.py                 # End-to-end reference solver tests
    ├── test_geometry.py                       # Bounding box and scene construction tests
    ├── test_incremental_updates.py            # Exact zero-error update tests
    ├── test_pedestrian_grid.py                # Grid index and coordinate mapping tests
    ├── test_ray_intersections.py              # Vectorized ray-AABB intersection tests
    ├── test_shadows.py                        # Direct shadow raycasting tests
    ├── test_solar_position.py                 # Astronomical solar position verification tests
    ├── test_solweig_reference.py              # Analytical reference comparison tests
    └── test_validation_comparisons.py         # Statistical comparison metric tests
```

---

