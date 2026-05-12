**Task Requirements:**

Run a test execution audit for the data-analyzer and todo-api projects. In code-server, open the integrated terminal, navigate into each project directory, and execute the project's test command (pytest tests/test_analyzer.py -v for data-analyzer and make test for todo-api). Parse each run's output and record: tests passed, tests failed, and pass rate percentage (passed / (passed + failed) * 100, rounded to two decimals). Create a Baserow database "Regression Test Audit March 2026" with a table "Test Execution Audit" containing fields Project (primary text), Tests Passed (number), Tests Failed (number), Pass Rate (number with 2 decimals), Pass/Fail (single-select: Pass/Fail), Captured At (date). Add exactly two rows — one per project — using the measured counts; set Pass/Fail to Pass if the pass rate >= 85.00 else Fail. In OpenProject project "product-catalog", create a single work package of type Task with subject "Test Execution Audit Report" and a description containing the measured pass rates, passed/failed counts, and whether each project passed or failed against the threshold 85.00.

**Steps:**

1. In code-server terminal, cd into data-analyzer and run pytest tests/test_analyzer.py -v, then parse the output to extract the number of tests passed and tests failed, and compute the pass rate percentage
2. Repeat for todo-api using make test
3. In Baserow, create "Regression Test Audit March 2026" with the "Test Execution Audit" schema (Project, Tests Passed, Tests Failed, Pass Rate, Pass/Fail, Captured At) and add exactly two rows populated with measured counts, computed pass rates, and Pass/Fail evaluated against 85.00
4. In OpenProject "product-catalog", create a single Task work package with subject "Test Execution Audit Report" and a description listing, for each of the two projects, the measured pass rate, passed/failed counts, and whether it passed or failed against the threshold 85.00

**Login Credentials:**

- code-server: (no username) / 8a128206e2177bce1e48e565
- baserow: admin@example.com / Admin1234
- openproject: admin / AdminPass123!
