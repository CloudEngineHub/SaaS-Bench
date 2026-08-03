**Task Requirements:**
The receiving office kept a delivery manifest: for each Grocy product below, the manifest records a batch number, which is supposed to be the exact name of the FarmOS harvest log the delivery came from. Audit this manifest against FarmOS.

For each product in the manifest, check in FarmOS (Logs → Harvest) whether a harvest log exists whose name is **exactly** the batch number from the manifest (character-for-character). If no harvest log with that exact name exists, edit the Grocy product and append `AUDIT FLAG: Missing FarmOS harvest log` to its description — keep the existing description text intact and add the flag after it. Do not modify products whose batch number matches an existing FarmOS harvest log. Product names refer to the Grocy product with that exact name.

**Delivery manifest (Grocy product → batch number):**

| Grocy product | Batch number |
|---|---|
| Sliced Beets | 2024 Beet Harvest — North Field Center Bed |
| Strawberries | 2024 Strawberry Harvest — Peak Week June 15 |
| Whole Kernel Corn | 2024 Sweet Corn Harvest — South Field 1 |
| Cherry Tomatoes By Sainsburys | 2024 Cherry Tomato Harvest — North Field West Bed 1 |
| Organic Peas & Shoestring Carrots | 2024 Carrot Harvest — North Field Center Bed 1 |
| Organic Green Beans | 2024 Green Bean Harvest — North Field East Bed 1 |
| Chestnut Mushrooms | 2024 Chestnut Mushroom Harvest — West Greenhouse 1 |
| Shreds Iceberg | 2024 Iceberg Lettuce Harvest — North Field East Bed 2 |

**Steps:**
1. For each manifest entry, look up the Grocy product and search the FarmOS harvest logs for the exact batch number.
2. Mark the entry as matched (a harvest log with that exact name exists) or unmatched.
3. For every unmatched product, edit it in Grocy and append `AUDIT FLAG: Missing FarmOS harvest log` to its description.

**Login Credentials:**

- grocy: admin / admin
- farmos: admin / admin123456
