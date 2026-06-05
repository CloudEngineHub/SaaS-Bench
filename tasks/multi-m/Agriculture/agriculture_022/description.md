**Task Requirements:**
In Grocy, retrieve the list of all products that carry a real batch identifier — concretely, entries in the `stock` table whose `stock_id` is **not** an auto-generated placeholder (i.e., `stock_id` does not start with `x`). For each such `stock_id`, query FarmOS via the JSON:API endpoint `/api/log/harvest` and check whether any harvest log has an `attributes.lot_number` value that **exactly** equals that `stock_id`. If a Grocy product's `stock_id` has NO matching FarmOS harvest log, you must do two things: 1) Add a note in the Grocy product description stating 'DISCREPANCY: No matching FarmOS harvest log found', and 2) Append '[REVIEW REQUIRED]' to the product name. Do not modify products whose `stock_id` has a matching FarmOS harvest log.

**Steps:**
1. Extract all batch identifiers — i.e., `stock_id` values from rows in Grocy's `stock` table where `stock_id` does not start with `x`.
2. For each `stock_id`, search FarmOS harvest logs for one whose `lot_number` attribute exactly equals it.
3. Identify the Grocy products whose `stock_id` values are missing from FarmOS harvest logs.
4. Flag the discrepant Grocy products by appending the discrepancy note to their description and `[REVIEW REQUIRED]` to their name.

**Login Credentials:**

- grocy: admin / admin
- farmos: admin / admin123456
