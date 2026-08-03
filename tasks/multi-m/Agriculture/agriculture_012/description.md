**Task Requirements:**

Create the EU-compliant digital wine label for the estate's organic Chardonnay 2023 in e-label.

The product form has two levels: a short **Create** form first, and a full **Edit** form (with the remaining sections) that becomes available after the record is created.

Step 1 — Create the wine record (Products → New product) with these exact values:

| Field | Required value |
|-------|---------------|
| Product name | `Boutique Organic Chardonnay` (do NOT include the vintage year in the name; the year goes in the separate Vintage field) |
| Net volume | `0.75` (the field expects **liters**: 750 mL = 0.75 L) |
| Vintage | `2023` |
| Type | `White` (this Chardonnay is a still white wine) |
| Appellation | `Loire` |
| Alcohol | `12.5` (enter the plain number; the public label renders it as "12.5 % vol.") |

Step 2 — Open the new product's **Edit** form (Products → the new record → Edit, or via its Details page) and complete:

- **Certifications** section → tick **Organic** (this wine is certified organic)
- **Food Business Operator** section → Name: `Boutique Organic Farm`
- **Ingredients** section → add the predefined ingredient `Sulphites` from the ingredient list (it is flagged as an allergen, which satisfies the EU allergen declaration)

Step 3 — Publish the label from the product's **Details** page:

- The Details page shows the auto-generated public e-label page link; open it and confirm it displays the wine data, including the alcohol shown as "12.5 % vol.".
- Download the product's QR code (SVG, PNG or JPEG) from the same Details page — this is the label's QR-code export.

**Steps:**
1. In e-label, create the `Boutique Organic Chardonnay` record with the exact Step-1 values (name without vintage; volume in liters; Type White).
2. On the product's Edit form, enable the Organic certification, set the Food Business Operator name to `Boutique Organic Farm`, and add the predefined `Sulphites` ingredient.
3. Open the product's Details page, confirm the public e-label page renders with the alcohol shown as "% vol.", and download the QR code.

**Login Credentials:**

- e-label: Admin / Admin2024!Pass
