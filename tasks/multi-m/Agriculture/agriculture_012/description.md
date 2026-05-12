**Task Requirements:**

Step 1 — Create a new wine record in e-label with all mandatory compliance fields:

| Field | Required value |
|-------|---------------|
| Producer | Farm/winery name as recorded in FarmOS (must match exactly) |
| Vintage | 2023 |
| AOC / Appellation | The certified organic production region for this farm |
| Grape Variety | Pinot Noir, 100% |
| Alcohol % | Must use format "13.5% vol" (not "13.5%" or "13.5度") |
| Net Volume | 750 mL |
| Allergens | Must include the text "Sulphites" or "亚硫酸盐" (exact substring) |

All seven mandatory fields must be non-empty. Missing even one makes the label non-compliant.

Step 2 — Fill consumer-facing sensory fields using sommelier-level domain inference:
Based on the declared grape variety (Pinot Noir) and its known profile, complete the following fields. Values must be grounded in Pinot Noir's actual characteristics — not generic defaults:

- Serving temperature: Pinot Noir is a light-bodied red; correct range is 12–16°C (not the 8–10°C used for white wines)
- Glass type: Burgundy glass (not Bordeaux glass — Pinot Noir's aromatics require a wider bowl)
- Food pairings: at least 2 specific dish names appropriate for Pinot Noir (e.g. duck breast with cherry sauce, mushroom risotto, Burgundy-style beef)
- Tasting description: ≤100 characters; must mention at least one of: aroma profile, tannin level, acidity, or finish of Pinot Noir

Step 3 — Export / generate the digital label preview with QR code:
After saving the record, trigger the QR-code PDF export. The output must contain a functional, scannable QR code embedded in the document — not a decorative graphic.

**Steps:**
1. In e-label, create a new wine record. Fill all 7 mandatory compliance fields as specified.
2. Use Pinot Noir domain knowledge to fill serving temperature (12–16°C), glass type (Burgundy), food pairings (≥2 specific dishes), and tasting description (≤100 chars mentioning aroma/tannin/acidity/finish).
3. Verify the Producer field exactly matches the farm/winery name already in FarmOS before saving.
4. Export the e-label record as a QR-code PDF.

**Login Credentials:**

- e-label: Admin / Admin2024!Pass
