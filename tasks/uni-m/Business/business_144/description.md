**Task Requirements:**

Execute a shift scheduling and overtime management workflow spanning shift configuration and assignment in Frappe HRMS, overtime cost accounting in BigCapital, and coordination task management in Twenty CRM.

In Frappe HRMS: (1) Create a Shift Type named 'Gamma Shift' with start time '06:30' and end time '14:30'. Enable auto-attendance from Employee Checkin. Set early exit grace period to 8 minutes and late entry grace period to 8 minutes. (2) Create a Shift Type named 'Sigma Shift' with start time '14:30' and end time '22:30'. Enable auto-attendance from Employee Checkin. Set early exit grace period to 8 minutes and late entry grace period to 8 minutes. (3) Create a Shift Type named 'Theta Shift' with start time '22:30' and end time '06:30'. Enable auto-attendance from Employee Checkin. Set the same grace periods. (4) Navigate to the Shift Type list and verify all three shift types exist with correct start/end times. (5) Using the Shift Assignment Tool, bulk assign 'Gamma Shift' to employees in department 'Finance & Accounting - TVS' for the date range 2026-09-01 to 2026-09-30. (6) Create individual Shift Assignments for the following employees on 'Sigma Shift' for dates 2026-09-01 to 2026-09-30: Kavitha Iyer, Arjun Nair, Ananya Reddy (3 employees). (7) Create individual Shift Assignments for the following employees on 'Theta Shift' for dates 2026-09-01 to 2026-09-30: Mohammed Farooq, Sanjay Krishnan (2 employees). (8) Process a Shift Request from employee 'Deepika Joshi' (HR-EMP-00010) requesting to change from 'Gamma Shift' to 'Sigma Shift' for date 2026-09-12. NOTE: Deepika Joshi belongs to department 'Finance & Accounting - TVS' and is NOT one of the employees in Kavitha Iyer, Arjun Nair, Ananya Reddy or Mohammed Farooq, Sanjay Krishnan. Create the shift request and approve it. (9) Navigate to the Shift Assignment list and verify: (a) active assignments exist for 'Gamma Shift' covering department 'Finance & Accounting - TVS' for 2026-09-01 to 2026-09-30; (b) individual assignments exist for each of Kavitha Iyer, Arjun Nair, Ananya Reddy on 'Sigma Shift'; (c) individual assignments exist for each of Mohammed Farooq, Sanjay Krishnan on 'Theta Shift'; (d) the approved Shift Request for Deepika Joshi is visible with status 'Approved'. (10) Create an Overtime Type named 'Night Differential Overtime' with pay rate multiplier 1.25. (11) Create an Overtime Slip for employee 'Suresh Menon' (HR-EMP-00009) with overtime type 'Night Differential Overtime', 6 hours, for date 2026-09-06. Submit the overtime slip. (12) Create an Overtime Slip for employee 'Rahul Verma' (HR-EMP-00013) with overtime type 'Night Differential Overtime', 4 hours, for date 2026-09-13. Submit the overtime slip.

In BigCapital: (13) Create an account 'Overtime Shift Differential Expense' of type 'Expense' if it does not already exist. (14) Verify that 'Accounts Payable (A/P)' exists as a liability-type account. If it does not exist, create it as a liability account named 'Accounts Payable (A/P)'. (15) The overtime costs are: OVERTIME_COST_1 = 375.00 (which equals 6 x 50 x 1.25), OVERTIME_COST_2 = 250.00 (which equals 4 x 50 x 1.25), TOTAL_OVERTIME = 625.00 (which equals 375.00 + 250.00). (16) Create and publish a manual journal entry dated 2026-09-30: debit 'Overtime Shift Differential Expense' for 625.00 and credit 'Accounts Payable (A/P)' for 625.00, memo 'Overtime accrual -- Suresh Menon (6h) + Rahul Verma (4h) -- rate 50 x 1.25 multiplier'. (17) Navigate to the General Ledger report filtered to account 'Overtime Shift Differential Expense' for date range 2026-09-30 to 2026-09-30. Verify a debit entry for 625.00 appears. (18) Navigate to the Profit and Loss Sheet for date range 2026-09-01 to 2026-09-30. Verify 'Overtime Shift Differential Expense' shows 625.00.

In Twenty CRM: (19) Create a task titled 'Review shift schedule compliance -- 2026-09-01 to 2026-09-30' with due date 2026-10-07 and body: 'Shift schedule deployed:
- Gamma Shift (06:30-14:30): Finance & Accounting - TVS department bulk assigned
- Sigma Shift (14:30-22:30): 3 employees assigned
- Theta Shift (22:30-06:30): 2 employees assigned
Shift swap approved: Deepika Joshi from Gamma Shift to Sigma Shift on 2026-09-12.
Review assignment records for compliance.' (20) Create a task titled 'Process overtime payments -- 2026-09-30' with due date 2026-10-14 and body: 'Overtime slips submitted:
- Suresh Menon: 6 hours on 2026-09-06 = 375.00 USD
- Rahul Verma: 4 hours on 2026-09-13 = 250.00 USD
Total: 625.00 USD
Journal entry posted 2026-09-30. Include in next payroll run.' (21) Create a note titled 'Shift & Overtime Summary -- 2026-09-01 to 2026-09-30' with body:
'SHIFT CONFIGURATION:
- Gamma Shift: 06:30-14:30, grace 8 min
- Sigma Shift: 14:30-22:30, grace 8 min
- Theta Shift: 22:30-06:30, grace 8 min

ASSIGNMENTS:
- Morning: Finance & Accounting - TVS department (bulk)
- Evening: Kavitha Iyer, Arjun Nair, Ananya Reddy
- Night: Mohammed Farooq, Sanjay Krishnan
- Swap: Deepika Joshi -> Sigma Shift on 2026-09-12

OVERTIME:
- Suresh Menon: 6h @ 50 x 1.25 = 375.00 USD
- Rahul Verma: 4h @ 50 x 1.25 = 250.00 USD
- Total: 625.00 USD
- Accrual: Overtime Shift Differential Expense (debit) / Accounts Payable (A/P) (credit)'

**Steps:**

1. In Frappe HRMS, create three shift types (morning 'Gamma Shift', evening 'Sigma Shift', night 'Theta Shift') with their respective start/end times (06:30-14:30, 14:30-22:30, 22:30-06:30), auto-attendance enabled, and grace periods of 8 minutes each.
2. Bulk assign 'Gamma Shift' to department 'Finance & Accounting - TVS' for 2026-09-01 to 2026-09-30. Create individual shift assignments for 3 evening shift employees (Kavitha Iyer, Arjun Nair, Ananya Reddy) and 2 night shift employees (Mohammed Farooq, Sanjay Krishnan) for the same date range. Process and approve a shift swap request for Deepika Joshi (who belongs to 'Finance & Accounting - TVS' and is not in the evening or night shift employee lists) from morning to evening shift on 2026-09-12.
3. Verify all shift assignments and the approved shift request in the Shift Assignment list. Create overtime type 'Night Differential Overtime' with multiplier 1.25. Create and submit overtime slips for Suresh Menon (6 hours on 2026-09-06) and Rahul Verma (4 hours on 2026-09-13).
4. In BigCapital, create expense account 'Overtime Shift Differential Expense' if needed. Verify 'Accounts Payable (A/P)' exists as a liability account, or create it if absent. Post a journal entry dated 2026-09-30 debiting 'Overtime Shift Differential Expense' for 625.00 and crediting 'Accounts Payable (A/P)' for 625.00 with the specified memo. Verify via General Ledger (debit of 625.00 on 'Overtime Shift Differential Expense') and Profit & Loss report ('Overtime Shift Differential Expense' shows 625.00).
5. In Twenty CRM, create a task titled 'Review shift schedule compliance -- 2026-09-01 to 2026-09-30' with shift deployment details and due date 2026-10-07. Create a task titled 'Process overtime payments -- 2026-09-30' with overtime cost breakdown using exact amounts (375.00, 250.00, 625.00) and due date 2026-10-14. Create a note titled 'Shift & Overtime Summary -- 2026-09-01 to 2026-09-30' with full shift configuration, assignment details, and overtime cost breakdown with exact amounts.

**Login Credentials:**

- frappe-hrms: Administrator / admin
- bigcapital: admin@bigcapital.local / admin123
- twenty: jane.austen@apple.dev / tim@apple.dev
