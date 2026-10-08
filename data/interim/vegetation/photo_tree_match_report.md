# Photo-to-Tree Matching and Visual Verification Report

## 1. Overview of Evaluated Imagery
This report documents the systematic spatial, temporal, and geometric cross-referencing between the 14 BBMP tree census records and available public street-level and aerial photographs of Church Street, Bengaluru.

- **KartaView 2020 Sequential Dashcam Imagery**: 29 street-level photographs captured on 2020-06-15 along Church Street (4032 x 3024 pixels, CC BY-SA 4.0).
- **Wikimedia Commons Ground and Aerial Photographs**: 8 high-resolution photographs spanning 2018 to 2024 (CC BY-SA 4.0), including street ground views and high-angle aerial views from the 22-story Barton Centre.
- **Mapillary Reference Material**: Crowdsourced 360-degree street capture sequence (Sequence key `860157968229406`, October 2021).
- **Total Processed Match Associations**: 77 evaluated tree-image pairs.

---

## 2. Spatial Correspondence and Vehicle Trajectory
The KartaView sequence (`2394274`, sequence indices 1363 to 1391) represents a continuous westward drive along Church Street:
- **Starting Point (Seq 1363)**: Local X = 284.1 m, Y = 34.3 m (Eastern approach near Brigade Road).
- **Ending Point (Seq 1391)**: Local X = -74.0 m, Y = 115.0 m (Western exit towards St. Mark's Road).
- **Camera Orientation**: Forward-facing along vehicle heading (282 deg to 285 deg azimuth, West-North-West).
- **Relative Tree Geometry**: All 6 core trees (T08 to T13) are located along the southern pedestrian walkway (Y in [65.5, 83.3] m), placing them consistently on the **driver's left-hand side** as the vehicle moves westward.

---

## 3. Core Cohort Matching Summary

| Tree ID | Census Species | Local Coord (X, Y) | Closest Image | Dist (m) | Match Classification | Confidence | Dimensional Utility |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| **T08** | *Ficus Religiosa L.* | (20.1 m, 81.1 m) | `kartaview_814425142`<br>`commons_72609328` | 13.2 m | `MATCH_CONFIRMED` | HIGH | High: Broad crown, prominent aerial roots, vehicle clearance scale. |
| **T09** | *Syzygium Cumini (L.) Skeels* | (44.9 m, 83.3 m) | `kartaview_814425130` | 5.6 m | `MATCH_CONFIRMED` | HIGH | High: Direct 5.6m roadside capture, trunk and dense crown clearly resolved. |
| **T10** | *Syzygium Cumini (L.) Skeels* | (33.2 m, 77.3 m) | `kartaview_814425138` | 14.5 m | `MATCH_CONFIRMED` | HIGH | Medium-High: Clear roadside view between T08 and T09. |
| **T11** | *Saraca Asoca De Wilde* | (60.9 m, 75.4 m) | `kartaview_814425114` | 11.1 m | `MATCH_CONFIRMED` | HIGH | High: Compact crown, tree grate and sidewalk curb clearly visible. |
| **T12** | *Saraca Asoca De Wilde* | (78.3 m, 74.6 m) | `kartaview_814425338` | 7.5 m | `MATCH_CONFIRMED` | HIGH | High: Upright crown, companion to T11, storefront scale reference. |
| **T13** | *Techoma Stans* | (97.1 m, 65.5 m) | `kartaview_814425266` | 12.2 m | `MATCH_CONFIRMED` | MEDIUM | Medium: Small rounded tree / large shrub in raised sidewalk planter. |

---

## 4. Context Cohort Matching Summary
- **T06 & T07 (*Araucaria columnaris*)**: Matched with `MATCH_PROBABLE` from images `kartaview_814425166` and `814425170` (14.2 to 19.4 m). Distinctive tall conical/columnar Cook Pine silhouettes.
- **T05 (*Ficus racemosa*)**: Matched with `MATCH_PROBABLE` from `kartaview_814425166` (19.0 m).
- **T03 & T04**: Distant canopy tops visible in Barton Centre aerial obliques (`commons_154346578`, `154346605`), classified as `MATCH_POSSIBLE`.
- **T01, T02, T14**: Obscured behind multi-story commercial buildings in alleyways/rear parcels; classified as `INSUFFICIENT_VIEW`.

---

## 5. Critical Methodological Findings & Safeguards
1. **Historical vs Current Existence**:
   - The street photographs date from **June 2020** (KartaView) and **June 2018** (Commons).
   - Under project scientific integrity rules: **Historical photographs do NOT prove current 2026 tree survival.**
   - All 14 trees retain `current_existence_status: CURRENT_EXISTENCE_UNCERTAIN` pending formal 2026 on-site verification.
2. **Camera Calibration**:
   - None of the camera images possess metric calibration or internal orientation parameters ($f, c_x, c_y, k_1, k_2$).
   - All derived dimensions are strictly **provisional photo-estimates** derived by comparative proportion scaling against adjacent known building floor heights (~3.5 m) and vehicular widths (~1.8 m).
   - No photo measurement may be treated as a survey-grade ground truth.
