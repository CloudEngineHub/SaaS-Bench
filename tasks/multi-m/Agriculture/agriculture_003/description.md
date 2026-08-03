**Task Requirements:**
In e-label, create a new digital wine label for the estate's 2024 Pinot Noir and complete its compliance data, so that the public e-label page and its QR code are generated.

The product form has two levels: a short **Create** form first, and a full **Edit** form (with the remaining sections) that becomes available after the record is created. Use the exact values below.

On the **Create** form (Products → New product):

| Field | Required value |
|-------|---------------|
| Product name | `Estate Pinot Noir` (do NOT include the vintage year in the name; the year goes in the separate Vintage field) |
| Net volume | `0.75` (the field expects **liters**: 750 mL = 0.75 L) |
| Vintage | `2024` |
| Type | `Red` (this Pinot Noir is a still red wine) |
| Appellation | `Burgundy` |
| Alcohol | `13.5` (enter the plain number; the public label renders it as "13.5 % vol.") |

After saving, open the new product's **Edit** form (Products → the new record → Edit, or via its Details page) and complete:

- **Food Business Operator** section → Name: `Boutique Organic Farm`
- **Ingredients** section → add the predefined ingredient `Sulphites` from the ingredient list (it is flagged as an allergen, which satisfies the EU allergen declaration)

Finally, publish the label assets from the product's **Details** page:

- Use **Change Image** to upload a product/label image for the record (any representative image file is acceptable, e.g. a bottle photo or a simple generated image).
- The Details page shows the auto-generated public e-label page link and its QR code; download the QR code (SVG, PNG or JPEG) — this is the label's QR-code export.

**Steps:**
1. In e-label, create the wine record with the exact values from the Create-form table (name without vintage; volume in liters).
2. Open the new product's Edit form and set the Food Business Operator name to `Boutique Organic Farm`.
3. On the same Edit form, add the predefined `Sulphites` ingredient to the product.
4. On the product's Details page, upload a product/label image via Change Image, confirm the public e-label page link opens, and download the QR code.

**Login Credentials:**

- e-label: Admin / Admin2024!Pass
