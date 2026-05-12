**Task Requirements:**

Step 1 — Visual analysis and keyword derivation:
Examine the dish photo (`tasks/multi-m/inputs/recipya_recipe_545.jpg`) carefully. Identify the dish type from: visible ingredients (colour, shape, texture), cooking style, regional cuisine cues. Derive 1–3 text search keywords that would locate this dish in a recipe database. Do not guess randomly — apply culinary domain knowledge (e.g. layered coloured vegetables in a French rustic style → consider "ratatouille" as the search term).

Step 2 — Recipya keyword search and match decision:
Search Recipya using the derived keyword(s). Decide whether a result constitutes a valid match: a match requires ≥70% ingredient overlap with the visible dish content (not just a similar name).

- **If a matching recipe is found:** read its full ingredient list with quantities from Recipya.
- **If no valid match is found:** identify at least 5 visible ingredients directly from the photo (with estimated quantities) and create a new recipe in Recipya (include: name, ≥5 ingredients, at least 4 cooking steps).

Step 3 — Grocy inventory check per ingredient:
For each ingredient in the recipe (from step 2), check current Grocy stock:
- Stock sufficient (> 500 g or > 5 units) → mark as "available"
- Insufficient or out of stock → add to Grocy shopping list with a note containing: required quantity AND restaurant name "Bistrot Provençal"

Step 4 — Create a Grocy Recipe:
In Grocy, create a new Recipe entry:
- Name: same as the Recipya recipe (matched or newly created)
- Ingredient list: linked to Grocy products (must match Recipya ingredient list; semantic matching required — "Aubergine" in Recipya may be "Eggplant" or "茄子" in Grocy)
- Upload the dish photo (`tasks/multi-m/inputs/recipya_recipe_545.jpg`) as the Recipe's image attachment (not as a product image)

**Steps:**
1. Examine the dish photo (`tasks/multi-m/inputs/recipya_recipe_545.jpg`); identify dish type and derive 1–3 text search keywords.
2. Search Recipya by keywords. Decide if a match exists (≥70% ingredient overlap). If no match, create a new Recipya recipe with ≥5 ingredients and ≥4 cooking steps.
3. For each ingredient in the confirmed recipe, check Grocy stock. Add out-of-stock items to the Grocy shopping list with quantity and note "Bistrot Provençal".
4. Create a Grocy Recipe with the same name as the Recipya recipe, full ingredient list linked to Grocy products, and the dish photo (`tasks/multi-m/inputs/recipya_recipe_545.jpg`) uploaded as the recipe image.

**Input files:**
- **File 1:** `tasks/multi-m/inputs/recipya_recipe_545.jpg`
  - Type: image
  - Role: dish_photo_from_restaurant_partner

**Login Credentials:**

- grocy: admin / admin
- recipya: admin@recipya.com / mw-admin-123
