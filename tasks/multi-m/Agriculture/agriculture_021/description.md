**Task Requirements:**
Iterate through all products in Grocy that have a batch number assigned in their 'batch_number' custom userfield. For each batch number, query FarmOS to see if a corresponding harvest log exists where the harvest log's name is the exact batch number. If a Grocy product's batch number has no match in FarmOS, edit the Grocy product to append 'AUDIT FLAG: Missing FarmOS harvest log' to its description field.

**Steps:**
1. Retrieve all batch numbers from Grocy products' custom userfields.
2. Cross-reference each batch number against FarmOS harvest log names.
3. For any unmatched batch, append the discrepancy flag to the Grocy product description.

**Login Credentials:**

- grocy: admin / admin
- farmos: admin / admin123456