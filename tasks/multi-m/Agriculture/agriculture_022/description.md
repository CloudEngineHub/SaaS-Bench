**Task Requirements:**
In Grocy, retrieve the list of all products that have a batch number assigned. For each batch number, query FarmOS to check if a Harvest log exists with that exact identical batch number. If you find a Grocy product whose batch number does NOT have a matching FarmOS harvest log, you must do two things: 1) Add a note in the Grocy product description stating 'DISCREPANCY: No matching FarmOS harvest log found', and 2) Change the product's active status or append '[REVIEW REQUIRED]' to the product name. Do not modify products that have valid matching logs.

**Steps:**
1. Extract all batch numbers currently used in Grocy products.
2. Search FarmOS Harvest logs for each batch number.
3. Identify any Grocy products with batch numbers missing from FarmOS.
4. Flag the discrepant Grocy products by updating their descriptions and appending '[REVIEW REQUIRED]' to their names.

**Login Credentials:**

- grocy: admin / admin
- farmos: admin / admin123456