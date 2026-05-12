**Task Requirements:**
In FarmOS, create an activity log on 'Vineyard Block 1' for spring plowing, upload the provided field photo as an attachment to the log, and record the batch number 'VINO-2025-001' in the notes. In Grocy, create a new product 'Organic Estate Wine 2025' and set its batch number (in the description or custom field) to exactly 'VINO-2025-001'. In e-label, draft a new wine record for 'Organic Estate Wine 2025' and set its batch number to 'VINO-2025-001'. The batch number must be character-for-character identical across all three systems.

**Steps:**
1. Log the spring plowing activity in FarmOS with the batch number and upload the field photo as an attachment.
2. Create the corresponding wine product in Grocy, ensuring the batch number is included.
3. Draft the compliance label in e-label using the exact same batch number.

**Input files:**
- **File 1:** `tasks/multi-m/inputs/farmos_crop_021.jpg`
  - Type: image/jpeg
  - Source app: farmos
  - Metadata:
    - log_name: Spring Plowing Complete
    - asset_name: Vineyard Block 1
    - notes: Plowed 120 acres. Soil conditions excellent. Ready for planting.

**Login Credentials:**

- farmos: admin / admin123456
- grocy: admin / admin
- e-label: Admin / Admin2024!Pass