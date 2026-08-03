**Task Requirements:**
The farm's organic audit requires reconciling the warehouse's delivery manifest against FarmOS harvest records. For each Grocy product below, the manifest records a batch number, which is supposed to be the exact name of the FarmOS harvest log the delivery came from.

For each product in the manifest, query FarmOS (Logs → Harvest) and check whether a harvest log exists whose name is **exactly** the batch number from the manifest (character-for-character). If a product's batch number has NO matching FarmOS harvest log, you must do two things: 1) append the note `DISCREPANCY: No matching FarmOS harvest log found` to the product's description (keep the existing description text intact and add the note after it), and 2) append `[REVIEW REQUIRED]` to the end of the product's name. Do not modify products whose batch number has a matching FarmOS harvest log. Product names refer to the Grocy product with that exact name.

**Delivery manifest (Grocy product → batch number):**

| Grocy product | Batch number |
|---|---|
| 365 Everyday Value, Fat Free Skim Milk | Cow Milk — Weekly Collection August Week 1 |
| Clover Honey | 2024 Honey Harvest — Hive A and B |
| Pure Raw Honey | 2024 Honey Harvest — Hive A and B |
| Black Forest Girl, Homemade Spaetzles, Egg Noodles | 2024 Egg Collection — Weekly Tally August Week 3 |
| Nonfat Greek Yogurt | 2024 Goat Milk Collection — Weekly Tally September Week 1 |
| Cottage Cheese | 2024 Sheep Milk Collection — Weekly Tally August Week 3 |
| Kfactor 22 Manuka Honey | 2024 Manuka Honey Harvest — Hive C |
| Monterey Jack Cheese | 2024 Cow Milk — Weekly Collection September Week 2 |

**Steps:**
1. For each manifest entry, look up the Grocy product and search the FarmOS harvest logs for the exact batch number.
2. Identify the products whose batch number is missing from the FarmOS harvest logs.
3. Flag each discrepant product: append the discrepancy note to its description and `[REVIEW REQUIRED]` to its name.

**Login Credentials:**

- grocy: admin / admin
- farmos: admin / admin123456
