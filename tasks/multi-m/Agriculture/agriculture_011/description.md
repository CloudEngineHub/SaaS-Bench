**Task Requirements:**

Step 1 — Sequential visual analysis:
Examine `tasks/multi-m/inputs/farmos_crop_043.jpg` first (full-field overview): note the overall canopy condition and whether infestation is detectable from distance. Then examine `tasks/multi-m/inputs/farmos_crop_044.jpg` (close-up of tassel/leaf sheath): look for dense aphid clusters, shed skins, and leaf damage. Combine both observations to determine severity using this table:

| Severity | Visual criteria | Intervention |
|----------|----------------|--------------|
| Low | Scattered insects, no clustering, no visible leaf damage | Monitor only, re-inspect in 3 days |
| Medium | Localised clusters, mild yellowing or leaf curl | Apply Neem Oil (OMRI-listed) |
| **High** | Dense insect mass at tassel/leaf sheath, shed skins visible | Apply Pyrethrin (OMRI-listed) |

Step 2 — Locate corn plant asset in FarmOS:
Find the existing corn / maize plant asset. It may appear under a Chinese name (e.g. '玉米-大棚1号') or an English name (e.g. 'Corn Greenhouse 1'). Confirm both names refer to the same single asset before proceeding — do not create a duplicate.

Step 3 — Create four logs (all field content must be in English):

**Log A — Emergency Observation Log (today):**
- Log type: Observation
- Asset: corn plant asset
- Attach `tasks/multi-m/inputs/farmos_crop_044.jpg` as the photo evidence
- In the notes field, record: (1) what tasks/multi-m/inputs/farmos_crop_043.jpg shows about overall canopy condition (note that it cannot confirm or rule out aphid density at distance), (2) what tasks/multi-m/inputs/farmos_crop_044.jpg shows about dense aphid clustering at the tassel/leaf sheath base (shed skins visible), (3) final severity determination: "High"
- Set a `severity` annotation to "High"

**Log B — Input Log (today):**
- Log type: Input
- Asset: corn plant asset (same as Log A)
- Notes must include: pesticide name "Pyrethrin (OMRI-listed)", application rate "200 mL/acre", organic certification number "OMRI-2023-PY-001", operator "Li Shifu", equipment "Power Sprayer No. 1"

**Log C — Follow-up Observation Log (today + 7 days):**
- Log type: Observation
- Asset: corn plant asset (same as Log A)
- Date must be exactly 7 calendar days after today (handle cross-month arithmetic correctly, e.g. Jan 27 + 7 = Feb 3, not Jan 34)
- Notes must describe: aphid count reduced by approximately 70%, recommend continued monitoring for 7 more days before deciding on re-application

**Log D — Maintenance Log (today):**
- Log type: Maintenance
- Asset: **equipment asset** "Power Sprayer No. 1" (NOT the corn plant asset)
- Notes: post-spray equipment cleaning with water rinse to prevent organic pesticide cross-contamination

**Steps:**
1. Examine tasks/multi-m/inputs/farmos_crop_043.jpg (full-field) and tasks/multi-m/inputs/farmos_crop_044.jpg (close-up) in sequence; document your observations.
2. Locate the existing corn plant asset in FarmOS (try both Chinese and English name variants).
3. Create Emergency Observation Log (today) on corn plant asset: attach tasks/multi-m/inputs/farmos_crop_044.jpg, record dual-image observations, state severity "High".
4. Create Input Log (today) on corn plant asset: include Pyrethrin, 200 mL/acre, cert# OMRI-2023-PY-001, operator Li Shifu, equipment Power Sprayer No. 1.
5. Create Follow-up Observation Log (today + 7 days) on corn plant asset: ~70% reduction, continued monitoring recommendation.
6. Create Maintenance Log (today) on the **equipment** asset "Power Sprayer No. 1": post-spray water rinse.

**Input files:**
- **File 1:** `tasks/multi-m/inputs/farmos_crop_043.jpg`
  - Type: image
  - Role: full_field_overview_corn
- **File 2:** `tasks/multi-m/inputs/farmos_crop_044.jpg`
  - Type: image
  - Role: close_up_aphid_infestation_tassel

**Login Credentials:**

- farmos: admin / admin123456
