**Task Requirements:**
A customer uploaded a photo of a dish: **Beef and Broccoli Stir-Fry** (Chinese cuisine). Build the traceability chain for the dish's primary green vegetable — broccoli — across Recipya, Grocy and FarmOS.

Step 1 — Recipya: search the recipe library for this dish. The library has no matching recipe yet, so create a new recipe:

- Name: `Beef and Broccoli Stir-Fry`
- Cuisine: Chinese
- Ingredients: include one line with broccoli (e.g. `500 g broccoli, cut into florets`) and one line with beef (e.g. `300 g beef sirloin, sliced`), plus any seasonings you like
- Save the recipe and note its numeric recipe ID (shown in the recipe page URL, e.g. `/recipes/301`)

Step 2 — Grocy: look up broccoli in the stock. There is no plain broccoli product yet, so:

- Create a new product named exactly `Broccoli`
- Record a purchase/receipt for it (any amount), so the product has stock on hand

Step 3 — FarmOS: open the most recent Harvest log for broccoli, `2024 Broccoli Harvest — North Field East Bed (Side Shoots)`. The supplying farm's organic certification number is `OMRI-ORG-2024-1187`. Edit this harvest log and add the certification number to its notes, so the harvest is linked to the farm's organic certification for the upcoming audit.

Step 4 — Grocy: open the `Broccoli` product and append to its description both the Recipya recipe ID from Step 1 and the OMRI certification number `OMRI-ORG-2024-1187` from Step 3.

**Steps:**
1. Identify the dish in the photo as Beef and Broccoli Stir-Fry; in Recipya, create the recipe exactly as specified and note its numeric ID.
2. In Grocy, create the `Broccoli` product and add stock via a purchase.
3. In FarmOS, edit the latest broccoli harvest log and add the OMRI certification number `OMRI-ORG-2024-1187` to its notes.
4. Back in Grocy, append the Recipya recipe ID and the OMRI certification number to the `Broccoli` product's description.

**Input files:**
- **File 1:** `tasks/multi-m/inputs/recipya_recipe_006.jpg`
  - Type: image/jpeg
  - Source app: recipya
  - Metadata:
    - name: Beef and Broccoli Stir-Fry
    - cuisine: Chinese

**Login Credentials:**

- recipya: admin@recipya.com / mw-admin-123
- grocy: admin / admin
- farmos: admin / admin123456
