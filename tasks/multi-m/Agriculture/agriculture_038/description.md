**Task Requirements:**
The warehouse kept a receiving manifest: for each Grocy product below, the manifest records a batch number, which is supposed to be the exact name of the FarmOS harvest log the goods were harvested in. Audit this manifest against FarmOS.

For each product in the manifest, check in FarmOS (Logs → Harvest) whether a harvest log exists whose name is **exactly** the batch number from the manifest (character-for-character). If no harvest log with that exact name exists, edit the Grocy product and append `DISCREPANCY: No FarmOS Harvest Log` to its description — keep the existing description text intact and add the discrepancy text after it. Do not modify products whose batch number matches an existing FarmOS harvest log. Product names refer to the Grocy product with that exact name.

**Receiving manifest (Grocy product → batch number):**

| Grocy product | Batch number |
|---|---|
| Boni Bio Apples | Honeycrisp Apple Harvest — East Orchard 2024 |
| Italian Style Diced Tomatoes | 2024 Beefsteak Tomato Harvest — North Field West Bed 1 |
| Diced Potatoes With Onion | 2024 Yellow Onion Harvest — North Field Center Bed |
| Stewed Tomatoes | 2024 Cherry Tomato Harvest — North Field West Bed 2 |
| Tomato Sauce | 2024 Cherry Tomato Harvest — North Field West Bed 3 |
| Gazpacho | 2024 Gazpacho Harvest — South Field 1 |
| Longan In Syrup | 2024 Longan Harvest — West Greenhouse 1 |
| 100% Juice Cranberry Blend | 2024 Cranberry Harvest — River Bottom Parcel 1 |

**Steps:**
1. For each manifest entry, look up the Grocy product and search the FarmOS harvest logs for the exact batch number.
2. Mark the entry as matched (a harvest log with that exact name exists) or unmatched.
3. For every unmatched product, edit it in Grocy and append `DISCREPANCY: No FarmOS Harvest Log` to its description.

**Login Credentials:**

- grocy: admin / admin
- farmos: admin / admin123456
