**Task Requirements:**
Iterate through all products in Grocy that have a batch number assigned in the custom userfield called 'batch_number' on the Product object. For each batch number, query FarmOS to confirm a harvest log exists whose 'name' exactly matches that batch number. If a Grocy product's batch number has no matching FarmOS harvest log name, append 'DISCREPANCY: No FarmOS Harvest Log' to the Grocy product description.

**Steps:**
1. Retrieve all batch numbers currently active in Grocy.
2. For each batch number, search FarmOS harvest logs for an exact match.
3. Identify products with unmatched batch numbers.
4. Append the discrepancy text to the description of the unmatched Grocy products.

**Login Credentials:**

- grocy: admin / admin
- farmos: admin / admin123456