**Task Requirements:**
Analyze the provided dish photo to identify the dish. Search Recipya using derived keywords to find the exact recipe. Read the ingredient list to identify the primary green vegetable ingredient. In Grocy, check the stock for this vegetable. Then, in FarmOS, find the most recent Harvest log for this vegetable and extract its OMRI certification number. Finally, return to Grocy, locate the vegetable's product, and append both the Recipya Recipe ID and the FarmOS OMRI certification number to the Grocy product description.

**Steps:**
1. Analyze the dish photo and locate the corresponding recipe in Recipya.
2. Identify the primary green vegetable as a key ingredient and check its status in Grocy.
3. Locate the latest harvest log for this vegetable in FarmOS and extract the OMRI cert number.
4. Update the Grocy product description with both the extracted OMRI cert number and the Recipya Recipe ID.

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