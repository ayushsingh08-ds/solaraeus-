# SOLARAEUS Data Manifest

Per **GLOBAL RULE 9**, this manifest records the URL, licence, access date, version, and checksum for every dataset utilized in the SOLARAEUS research protocol.

Per **GLOBAL RULE 1**, only **Berlin (primary)**, **Chicago (fallback + replication)**, and **London (reference + replication)** are admissible case study sites. All legacy data (Church Street / Bengaluru) is strictly excluded and cannot be used as evidence.

---

## 1. Primary Case Study: Berlin (Friedrichstraße / Gendarmenmarkt Corridor)

- **City**: Berlin, Germany
- **Corridor**: Friedrichstraße between Französische Str. and Mohrenstr. (Berlin-Mitte)
- **Coordinates**: 52.5145° N, 13.3888° E
- **CRS**: EPSG:25833 (ETRS89 / UTM Zone 33N), Vertical Datum DHHN2016
- **Domain**: 240 m × 200 m, 48,000 cells at 1.0 m resolution
- **Data Layers**:
  - **Buildings (LoD2 CityGML)**:
    - Source: Geoportal Berlin / Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen
    - URL: `https://daten.berlin.de/datensaetze/geoportal-berlin-3d-gebaeudedaten`
    - Licence: dl-de/by-2-0 (Datenlizenz Deutschland – Namensnennung – Version 2.0)
    - Access Date: 2026-10-13
    - Version: LoD2 2024 Release
    - Local Processed Array: `data/processed/berlin/baseline_svf.npy` (SHA256: `376609d3eaf6e1a73887856b312009514f4608b7700fe3224f261f977010103b`)
  - **Terrain (DGM1)**:
    - Source: Geoportal Berlin Digitales Geländemodell (DGM 1m)
    - URL: `https://daten.berlin.de/datensaetze/digitales-gelaendemodell-dgm-1-m`
    - Licence: dl-de/by-2-0
    - Access Date: 2026-10-13
    - Elevation: Flat Spree valley plain ($z = 34.2\,\mathrm{m}$ DHHN2016; local datum $z = 0.0\,\mathrm{m}$)
  - **Vegetation (Baumkataster)**:
    - Source: Geoportal Berlin Baumbestand Berlin – Straßenbäume
    - URL: `https://daten.berlin.de/datensaetze/baumbestand-berlin-strassenbaeume`
    - Licence: dl-de/by-2-0
    - Access Date: 2026-10-13
    - Inventory: 16 roadside *Tilia cordata* (Littleleaf linden) trees ($h=9.5\,\mathrm{m}, r=3.5\,\mathrm{m}, \tau=0.15$)
  - **Weather Forcing (24-Hour Diurnal Summer Heatwave)**:
    - Source: Deutscher Wetterdienst (DWD) Open Data via `wetterdienst` Python API
    - Station: Station 00433 (Berlin-Tempelhof, 52.4675° N, 13.4021° E, 5.2 km from site)
    - Date of Observation: 2023-07-09 (Clear-sky peak summer heatwave, peak $T_{\mathrm{air}} = 32.1^\circ\mathrm{C}$)
    - URL: `https://opendata.dwd.de/climate_environment/CDC/`
    - Licence: Open Data / DWD (§ 4–6 DWD-Gesetz)
    - Local File: `data/raw/berlin/weather_24h.csv`
    - SHA256 Checksum: `59b9b53ac8cfbe43700a086e366367c39d4b23ff63490686c78762082621ced2`
  - **Baseline Literature Reference**:
    - Citation: Eingrüber, Meier, & Scherer (2025) *Geosci. Model Dev.*, 18, 141–160; Meier et al. (2017) TU Berlin
    - Baseline Range: Solar noon sunlit $T_{\mathrm{mrt}} \approx 57.0\text{–}61.5^\circ\mathrm{C}$, shaded $T_{\mathrm{mrt}} \approx 32.0\text{–}36.5^\circ\mathrm{C}$, $\Delta T_{\mathrm{mrt}} \approx 23.0\text{–}26.5\text{ K}$

---

## 2. Fallback & Replication Study: Chicago (S LaSalle Financial Canyon)

- **City**: Chicago, Illinois, USA
- **Corridor**: S LaSalle St between W Adams St and W Jackson Blvd (The Loop)
- **Coordinates**: 41.8795° N, -87.6324° W
- **CRS**: EPSG:32616 (WGS 84 / UTM Zone 16N), Vertical Datum NAVD88
- **Domain**: 240 m × 200 m, 48,000 cells at 1.0 m resolution
- **Data Layers**:
  - **Buildings**:
    - Source: City of Chicago Open Data Portal Building Footprints
    - URL: `https://data.cityofchicago.org/Buildings/Building-Footprints/`
    - Licence: Public Domain / City of Chicago Data Terms of Use
    - Access Date: 2026-10-13
    - Heights: 45.0 m to 110.0 m high-rise masonry and glass canyon
  - **Terrain**:
    - Source: USGS 3D Elevation Program (3DEP) 1m DEM
    - URL: `https://www.usgs.gov/3d-elevation-program`
    - Licence: Public Domain (US Federal Government)
    - Access Date: 2026-10-13
    - Elevation: Flat Lake Michigan terrace ($z = 181.5\,\mathrm{m}$ NAVD88; local datum $z = 0.0\,\mathrm{m}$)
  - **Vegetation**:
    - Source: City of Chicago Urban Forest Tree Inventory
    - Justified Approximation: 8 *Gleditsia triacanthos* (honey locust) sidewalk tree planters ($h=5.0\,\mathrm{m}, r=2.0\,\mathrm{m}$)
  - **Weather Forcing (24-Hour Diurnal Summer Heatwave)**:
    - Source: NOAA Local Climatological Data (LCD) Station KORD / Chicago O'Hare
    - Date of Observation: 2024-07-15 (Peak summer heatwave, peak $T_{\mathrm{air}} = 33.8^\circ\mathrm{C}$)
    - URL: `https://www.ncei.noaa.gov/cdo-web/`
    - Licence: Open Access / US Federal Government
    - Local File: `data/raw/chicago/weather_24h.csv`
    - SHA256 Checksum: `dde39d7ba67e6a9ed5bd9864403b6d1db1cfdd50c158070e5cc1df5703015324`
  - **Baseline Literature Reference**:
    - Citation: Middel et al. (2021) *Environ. Res. Lett.*; Sailor et al. (2015)
    - Baseline Range: Sunlit $T_{\mathrm{mrt}} \approx 58.5\text{–}63.0^\circ\mathrm{C}$, shaded $T_{\mathrm{mrt}} \approx 32.5\text{–}36.5^\circ\mathrm{C}$, $\Delta T_{\mathrm{mrt}} \approx 24.0\text{–}28.0\text{ K}$

---

## 3. Reference & Replication Study: London (Exhibition Road Boulevard)

- **City**: London, United Kingdom
- **Corridor**: Exhibition Road between Cromwell Rd and Prince Consort Rd (South Kensington)
- **Coordinates**: 51.4985° N, -0.1738° W
- **CRS**: EPSG:27700 (OSGB36 / British National Grid), Vertical Datum ODN
- **Domain**: 240 m × 200 m, 48,000 cells at 1.0 m resolution
- **Data Layers**:
  - **Buildings**:
    - Source: Ordnance Survey Open Map – Local / GLA 3D Building Heights
    - URL: `https://osdatahub.os.uk/`
    - Licence: Open Government Licence (OGL v3.0)
    - Access Date: 2026-10-13
    - Heights: 22.0 m to 32.0 m institutional Victorian limestone buildings
  - **Terrain**:
    - Source: Environment Agency LiDAR Composite DTM (1m)
    - URL: `https://environment.data.gov.uk/`
    - Licence: Open Government Licence (OGL v3.0)
    - Access Date: 2026-10-13
    - Elevation: South terrace ($z = 21.0\,\mathrm{m}$ ODN; local datum $z = 0.0\,\mathrm{m}$)
  - **Vegetation**:
    - Source: Royal Borough of Kensington & Chelsea Street Tree Dataset
    - Inventory: 14 *Platanus x hispanica* (London plane) boulevard trees ($h=11.0\,\mathrm{m}, r=4.0\,\mathrm{m}, \tau=0.18$)
  - **Weather Forcing (24-Hour Diurnal Summer Heatwave)**:
    - Source: Met Office MIDAS Open / London Heathrow (EGLL)
    - Date of Observation: 2024-07-19 (Peak clear heatwave, peak $T_{\mathrm{air}} = 32.2^\circ\mathrm{C}$)
    - URL: `https://catalogue.ceda.ac.uk/`
    - Licence: Open Government Licence (OGL v3.0)
    - Local File: `data/raw/london/weather_24h.csv`
    - SHA256 Checksum: `3a30a8a952abec1990dd1c7e531722796b4496a4322ea001e8c2238048085e44`
  - **Baseline Literature Reference**:
    - Citation: Lindberg et al. (2018) *Urban Climate*, 23, 1–19 (UMEP / SOLWEIG Central London)
    - Baseline Range: Sunlit $T_{\mathrm{mrt}} \approx 55.5\text{–}59.8^\circ\mathrm{C}$, shaded $T_{\mathrm{mrt}} \approx 31.5\text{–}35.0^\circ\mathrm{C}$, $\Delta T_{\mathrm{mrt}} \approx 22.0\text{–}25.5\text{ K}$

---

## 4. Processed Diurnal Simulation Artifacts (Stage 2)

- **Berlin Diurnal Metrics**: `data/processed/berlin/diurnal_metrics.json`
  - SHA256: `76be74a39fac77669fed1da985cd3582a9dd5f674fdcd8cf1d8e1d9997589f34`
- **Chicago Diurnal Metrics**: `data/processed/chicago/diurnal_metrics.json`
  - SHA256: `f1c2eb66aef6ed3899045d897491616b4880e1ba80c01a1767c49e0ceacdbbf2`
- **London Diurnal Metrics**: `data/processed/london/diurnal_metrics.json`
  - SHA256: `f577c8f1645ce785ddb0d8fd39d7213189088df423865fb14565e946ca3bcbfe`

## 5. Stage 3 Physics Validation & Benchmark Artifacts

- **Berlin SOLWEIG Comparison Figure**: `results/raw/stage_3/berlin_solweig_comparison.png`
  - SHA256: `08abe0ffe315e4297b3f7fc01b0c7dc1677ab1b9fba968365e5ddeb1048e0a4b`
- **Limiting-Cases Summary Figure**: `results/raw/stage_3/limiting_cases_validation.png`
  - SHA256: `52113800d68d9369c1a69593756c901c68083d1ce1419b7d0a74942d604a55a3`
- **Validation Metrics Summary JSON**: `results/raw/stage_3/validation_metrics.json`
  - SHA256: `77c155bb96e84d5d08c38a4cd36bebbd77cfad149d7c3461c997eebabb910b10`
- **Stage 3 Validation Test Suite**: `tests/test_stage_3_physics_validation.py`
  - SHA256: `d760420cce25e641c2948a920331dc81f5dd6e6510aa6aaa62f89fc7d138e084`
- **Stage 3 Benchmark Runner**: `benchmarks/run_stage_3_solweig_comparison.py`
  - SHA256: `0ec11a8a8cf0dc5ebf61e3e40cb16387139a9b3e671c71f89d029cd476845c21`
- **Stage 3 Research Report**: `docs/stage_3_report.md`
  - SHA256: `ac994d604cf5ee70a8e9bb524241839e0a0b9793fbf41780b7082bc5c67d4fb2`

## 6. Stage 4 Adversarial Stress & Certification Artifacts

- **Adversarial Error & Recomputation Maps Figure**: `results/raw/stage_4/adversarial_error_maps.png`
  - SHA256: `3a11708f5a9bccb06c6052fc484c266fb7d0ea7943bd18b8bb89e301ee7cb613`
- **Certificate Soundness Scatter Figure**: `results/raw/stage_4/bound_soundness_scatter.png`
  - SHA256: `28aac51777875898138ba8c5a557c67e98de6e003145ac8583b702a106a6a1b3`
- **Stage 4 Quantitative Metrics Summary JSON**: `results/raw/stage_4/stage_4_metrics.json`
  - SHA256: `ffd51d4edeed8079958a97bac0d55274f9c14d2e6766976371995d651842ec40`
- **Stage 4 Adversarial Validation Test Suite**: `tests/test_stage_4_adversarial_validation.py`
  - SHA256: `9ba55601d24cafd186e5fbdf34b3e22a0e2a007687d3788ed737ebe746fb14a0`
- **Stage 4 Adversarial Benchmark Runner**: `benchmarks/run_stage_4_adversarial_suite.py`
  - SHA256: `4bcf96a0f23fc7e4c1b02137a94a2ff4923ae36cbf0a439507d9899686f28b46`
- **Stage 4 Research Report**: `docs/stage_4_report.md`
  - SHA256: `e477487729c1db42022be566b1717d36ec707c2acb13c1691eb8a0e36d9c965b`

---

## 7. Stage 5 Performance & Scalability Artifacts

- **Master Performance Metrics JSON**: `results/raw/stage_5/stage_5_performance_metrics.json`
  - SHA256: `b8a787d36b9fcd8a4e3920207a4c340525b39bf5392a2e89327b6b9f22f388e8`
- **Latency Breakdown Figure**: `results/raw/stage_5/stage_5_latency_breakdown.png`
  - SHA256: `e015b7de51e899714725a57ddf0d85f961b2b8687afc2d39603c7f530c7d2fd7`
- **Speedup Comparison Figure**: `results/raw/stage_5/stage_5_speedup_comparison.png`
  - SHA256: `645b559a419690433984f9bea2924b47e4d36ed31cb9e8842242ebb1d57424f6`
- **Reuse Fraction Sweep Figure**: `results/raw/stage_5/stage_5_reuse_sweep.png`
  - SHA256: `ce98bf99eb9779d4f550a09eaec3c10b108ef1a905f380e3ec48b25fe0676dea`
- **CPU Micro-Benchmark Results JSON**: `results/raw/stage_5/benchmark_cpu_results.json`
  - SHA256: `c3c555dff92ddac9a11a9b7ada25e75f627c83867cd5e976522c448a251cbd08`
- **GPU Micro-Benchmark Results JSON**: `results/raw/stage_5/benchmark_gpu_results.json`
  - SHA256: `48ea2b279c51ff4e35c61e08aeef6b0811d5d7847ad5f7761144da94e790070d`
- **Master Benchmark Suite**: `benchmarks/run_stage_5_performance_suite.py`
  - SHA256: `fbe9c714985e24abe3e5570c2efd5ba27be02fcc754570c721b014f0598fd1ad`
- **GPU Benchmark CLI**: `benchmarks/benchmark_gpu.py`
  - SHA256: `efb453a0f6f99cd209d655180e38e7ef5a8c10c10608feb2002ff9df2e53e7c7`
- **CPU Benchmark CLI**: `benchmarks/benchmark_cpu.py`
  - SHA256: `4caa1500fee4a6a937a3a2ac0f652504ecab0bee3c4c984b1b86afefe66e5c8b`
- **POSIX CPU Benchmark Runner**: `benchmarks/benchmark_cpu.sh`
  - SHA256: `af467aa28ff91dff8fabcb658125574e627cfa625a5158b8ba1f64bc4b2341f9`
- **PowerShell CPU Benchmark Runner**: `benchmarks/benchmark_cpu.ps1`
  - SHA256: `b88b46964926fd51b9f79d3ca30da93cd30de73045afa36edb2d993994a2aa7c`
- **Stage 5 Performance Validation Suite**: `tests/test_stage_5_performance_validation.py`
  - SHA256: `3f32b6063792a686e6656b6f3ac8fabe7c2fb62ca90b77f66365c6dde2675e52`
- **Stage 5 Performance Engineering Report**: `docs/stage_5_report.md`
  - SHA256: `f142097cb42ed88f15a519e1c3cb9d32dea331cc06d8a7dee21798e1927737b0`

## 8. Stage 6 Optimization & Active Learning Artifacts

- **Master Optimization Metrics JSON**: `results/raw/stage_6/stage_6_optimization_metrics.json`
  - SHA256: `46ddd041a3a5edb6bbe7608ee88466ca944a53015133ed17505a11beb5289982`
- **Optimization Convergence Figure**: `results/raw/stage_6/stage_6_convergence_comparison.png`
  - SHA256: `b9d194f0f778f0b88d6f057f45e0c14dab9371386b7aac09dc506755e4e3d349`
- **Method Comparison Benchmarks Figure**: `results/raw/stage_6/stage_6_method_benchmarks.png`
  - SHA256: `8c66ccf9d8c7b94069205aed47d9db0fbbb39932437def52bb8391e7bca47323`
- **Tiny Problem Landscape Optimality Figure**: `results/raw/stage_6/stage_6_tiny_problem_optimality.png`
  - SHA256: `5c02ebd2023267366e12ef2a1719f7eb9379aa817d2d07dade409e32ef25b95d`
- **Optimal Canopy Layout Spatial Map**: `results/raw/stage_6/stage_6_optimal_layout_map.png`
  - SHA256: `e94c640f539f98d8e0315568ddd5bd3f97ab0f08e9c31f40776c8c27e7338a94`
- **Surrogate Parity Scatter Plot**: `results/raw/stage_6/stage_6_surrogate_parity.png`
  - SHA256: `b0f247c1cc74d9a22c4ebd92843c46872fc42304f8bcbd44494acf9ac5423331`
- **Optimization Problem Formulation Module**: `src/solaraeus/optimizer/problem.py`
  - SHA256: `0764fc9785d2c69bbdb22bd1801036531d63ee5fb31e3b78963251ea8a7412cf`
- **Optimization Algorithms Implementation**: `src/solaraeus/optimizer/algorithms.py`
  - SHA256: `e142f717420d3996b5f64856fb7bf469c4f8eb3287af1813f068fbc40ea18f2e`
- **Optimizer Package Initialization**: `src/solaraeus/optimizer/__init__.py`
  - SHA256: `a2e0df02b651a5a9aa1b095096c02c58c7457638561844be083c60d15b17a890`
- **Stage 6 Master Benchmark Suite**: `benchmarks/run_stage_6_optimization_suite.py`
  - SHA256: `9d1ee3eff4eb39aac4971e694a05ad0a53f6bc4e820790fb9df455d6edf2e77e`
- **Stage 6 Optimization Validation Suite**: `tests/test_stage_6_optimization_validation.py`
  - SHA256: `9bb984db5cf395a68ab1cdab1f8cc22453706a57eb630a9c745d9fdb500d4c5e`
- **Stage 6 Optimization Engineering Report**: `docs/stage_6_report.md`
  - SHA256: `7369dd3610c01d5ef1a068396a0543bffe911f457ad92b7ba91d07fa1cc3899b`

---

## 9. Stage 7 Comprehensive Evaluation & Replication Artifacts

- **Master Evaluation Metrics JSON**: `results/raw/stage_7/stage_7_evaluation_metrics.json`
  - SHA256: `3c3f62d4b31c23cfe04a541c2d3ba6d3a34148305bbd2bd4731040fcd4d3bc62`
- **Berlin Corridor Cooling Maps Figure**: `results/raw/stage_7/stage_7_berlin_cooling_maps.png`
  - SHA256: `8c83e8e101a35586ea88984286479c758cf0df97bb3905aa7c572e408451a9f7`
- **Multi-City Replication Comparison Figure**: `results/raw/stage_7/stage_7_replication_comparison.png`
  - SHA256: `b8331ae2949f31efbdca55f0941abb3614afe5c012def9b6c0b8d6c6b3f369fc`
- **Sensitivity Tornado Diagram Figure**: `results/raw/stage_7/stage_7_sensitivity_tornado.png`
  - SHA256: `ce0b2d1e2fc7f2a891be44519aadd008b84ce66d3e80259e4d30284d12aff7ed`
- **Geometric Shade Consistency Figure**: `results/raw/stage_7/stage_7_shade_consistency.png`
  - SHA256: `d824e4af1ad2f7d46807fe010d6fb149ca5dfe40fd9cf383cb12a4be810d1fe0`
- **Berlin Baseline Tmrt Array**: `results/raw/stage_7/berlin_baseline_tmrt.npy`
  - SHA256: `d99e834d7d5378fee29ee37017fe3ef40d861bf361234764f17c64d23ddbeff3`
- **Berlin Baseline UTCI Array**: `results/raw/stage_7/berlin_baseline_utci.npy`
  - SHA256: `305fdcb4c4b2b93195ce92ea784682fc910a11f2e7c16063286be1e621ffe171`
- **Berlin Optimised Tmrt Array**: `results/raw/stage_7/berlin_optimised_tmrt.npy`
  - SHA256: `60978ea613d220ae7747100e61456f7434fbe540c5cc6bcd78263918593005e6`
- **Berlin Optimised UTCI Array**: `results/raw/stage_7/berlin_optimised_utci.npy`
  - SHA256: `cfcc5b7558608bc6935c017df7c5007b53f75129e45f48751c81035c61009883`
- **Berlin Delta Tmrt Array**: `results/raw/stage_7/berlin_delta_tmrt.npy`
  - SHA256: `b52eaf19800566990d9daa011bdae387b0bc3f58f1f200df5beac9472d03ee7c`
- **Berlin Delta UTCI Array**: `results/raw/stage_7/berlin_delta_utci.npy`
  - SHA256: `c26099252eb66e0631d1d2c6c2abcd361f71e2e8c8ab30a14f9141e32d49af85`
- **Chicago Baseline Tmrt Array**: `results/raw/stage_7/chicago_baseline_tmrt.npy`
  - SHA256: `2c147bb293a15b0467a1b993cca5f6a6f9288d6863b57b6c5be9cdd4e4adb527`
- **Chicago Optimised Tmrt Array**: `results/raw/stage_7/chicago_optimised_tmrt.npy`
  - SHA256: `81f7b9eb43b963e8b771c1e06f32d9705fd2b441f26a1d75e710661b61980c11`
- **Chicago Delta Tmrt Array**: `results/raw/stage_7/chicago_delta_tmrt.npy`
  - SHA256: `e81a9f744e97382c4a032352c5bd1986118ef6af087cb786d3bafbaf5d9c0b07`
- **London Baseline Tmrt Array**: `results/raw/stage_7/london_baseline_tmrt.npy`
  - SHA256: `07929db74d5233bdc5a8ce9c9e22cc768597fd1fb3317c684d1aa16a9c89526c`
- **London Optimised Tmrt Array**: `results/raw/stage_7/london_optimised_tmrt.npy`
  - SHA256: `5cf8310fc8d2f03776fd59e50ca8bcb048fbbaaad91c4fc02eecaac6e12ac240`
- **London Delta Tmrt Array**: `results/raw/stage_7/london_delta_tmrt.npy`
  - SHA256: `786b0b35ccdc3cdb0e380a7cf959c1e0310a586a25cfa545ee1fdbe052e5ed99`
- **Stage 7 Master Evaluation Pipeline**: `benchmarks/run_stage_7_pipeline.py`
  - SHA256: `b8bc57fe4e0bc570dcf35ab76ac82cee65d4f4a8c62360a6a1b7fcebfd86a15f`
- **Stage 7 Validation Test Suite**: `tests/test_stage_7_evaluation_validation.py`
  - SHA256: `0a2d7dfce5d247aafdc27ce6365b8a550454f7ae8314a4e9aa9c4c7e05dae4ba`
- **Stage 7 Comprehensive Evaluation Report**: `docs/stage_7_report.md`
  - SHA256: `50254933c5ad9c4609c418e008214d24de608ebb528f16cf7334a8d17d1193ca`

---

## 10. Stage 8 Quality Assurance & Release Artifacts

- **Stage 8 QA & Reproducibility Report**: `docs/stage_8_report.md`
  - SHA256: `57e48b8f07721aceea171e75ea5c20058baa305a9c651f0176b3f49ac1732e81`
- **Master Project README**: `README.md`
  - SHA256: `7f7e5d997de7bef71c7a9fed84d56f3ab54ee1f8291ec52a5f43834963b8ca6c`
- **Clean Scientific Manuscript**: `research_paper_sol/solaraeus.tex`
  - SHA256: `6cfffb747ddeb503c28370a2603ef637de152ea9ef6bf06a05fd0076fd0c7175`

---

## 11. Deprecated / Legacy Sites Archive
- **Site**: Church Street (Bengaluru)
- **Classification**: DEPRECATED & OUT OF SCOPE per Global Rule 1.
- **Protocol Notice**: No legacy Church Street datasets are used as scientific evidence in this protocol.


