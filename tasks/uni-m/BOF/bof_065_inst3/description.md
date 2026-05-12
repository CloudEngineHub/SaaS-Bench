**Task Requirements:**

Execute a financial audit preparation workflow spanning accounting statement generation and reconciliation, HR payroll and employee data verification, and CRM documentation compilation. In BigCapital: (1) Navigate to the Trial Balance Sheet report filtered to the date range 2026-01-01 to 2026-12-31 with accounting basis 'Accrual'. Export the report as PDF. Record the total debits and total credits to confirm they balance. (2) Navigate to the Balance Sheet report filtered to as-of date 2026-12-31 with accounting basis 'Accrual'. Export the report as PDF. Record total assets, total liabilities, and total equity. (3) Navigate to the Profit and Loss Sheet report filtered to date range 2026-01-01 to 2026-12-31 with accounting basis 'Accrual'. Export the report as PDF. Record total revenue, total expenses, and net income. (4) Navigate to the Cash Flow Statement filtered to date range 2026-01-01 to 2026-12-31. Export the report as PDF. Record net cash from operating activities. (5) Navigate to the Journal Sheet report filtered to date range 2026-01-01 to 2026-12-31. Export the report as PDF. (6) Navigate to the General Ledger report filtered to account 'Bank Account' for date range 2026-01-01 to 2026-12-31. Verify the closing balance matches -$215,382.44. Export the report as PDF. (7) Navigate to the A/R Aging Summary report filtered to as-of date 2026-12-31. Export the report as PDF. Record the total outstanding receivables. (8) Navigate to the A/P Aging Summary report filtered to as-of date 2026-12-31. Export the report as PDF. Record the total outstanding payables. (9) Navigate to the Sales Tax Liability Summary report filtered to date range 2026-01-01 to 2026-12-31. Export the report as PDF. (10) Lock all transactions before date 2027-01-01 to prevent modifications to audited periods. Verify the locking status shows transactions are locked. In Frappe HRMS: (11) Navigate to the Employee Information report filtered by company 'TechVista Solutions Pvt. Ltd.'. Export the employee information to CSV. Record the total number of active employees. (12) Navigate to the Salary Register report filtered to the month of March and company 'TechVista Solutions Pvt. Ltd.'. Record the total gross earnings, total deductions, and total net pay across all employees. Export the salary register. (13) Navigate to the Income Tax Deductions report filtered by company 'TechVista Solutions Pvt. Ltd.' and payroll period '2026'. Record the total income tax deducted for the year. (14) Navigate to the Provident Fund Deductions report filtered by company 'TechVista Solutions Pvt. Ltd.' and payroll period '2026'. Record the total PF deductions. (15) Navigate to the Employee Leave Balance Summary report filtered by company 'TechVista Solutions Pvt. Ltd.'. Record the total outstanding leave balances across all employees for leave type 'Sick Leave'. This represents a potential liability. (16) Navigate to the Employee Advance Summary report. Verify that no employee advances remain with status 'Unpaid' or have unclaimed balances exceeding $750. Record any exceptions. In Twenty CRM: (17) Navigate to the Opportunities list. Filter by stage 'Won' and close date within 2026-01-01 to 2026-12-31. Sort by amount descending. Record the total count and total revenue of Won deals for the fiscal year. (18) Create a note titled 'Audit Preparation Package — FY 2026' with body containing all captured numeric values: 'Financial Statements Generated (all exported as PDF):
- Trial Balance: Total Debits = [value from step 1], Total Credits = [value from step 1], balanced confirmed
- Balance Sheet as of 2026-12-31: Total Assets = [value from step 2], Total Liabilities = [value from step 2], Total Equity = [value from step 2]
- P&L 2026-01-01 to 2026-12-31: Total Revenue = [value from step 3], Total Expenses = [value from step 3], Net Income = [value from step 3]
- Cash Flow Statement: Net Cash from Operating Activities = [value from step 4]
- Journal Sheet: All entries for the period exported
- General Ledger (Bank Account): Closing balance verified at -$215,382.44
- A/R Aging as of 2026-12-31: Total Outstanding Receivables = [value from step 7]
- A/P Aging as of 2026-12-31: Total Outstanding Payables = [value from step 8]
- Sales Tax Liability: Exported

Transaction Lock: All transactions before 2027-01-01 locked.

HR Verification:
- Active employees: [count from step 11]
- Final payroll (March): Gross Earnings = [value from step 12], Total Deductions = [value from step 12], Net Pay = [value from step 12]
- Income tax deducted (2026): [value from step 13]
- PF deductions (2026): [value from step 14]
- Outstanding leave liability (Sick Leave): [value from step 15]
- Employee advances: [exceptions from step 16 or "No unclaimed advances above $750"]

CRM Revenue:
- Won deals FY 2026: Count = [value from step 17], Total Revenue = [value from step 17]' (19) Create a task titled 'Submit audit package to external auditors — FY 2026' with due date 2027-03-15 and body: 'All financial statements, HR payroll reports, and CRM revenue summaries have been compiled. Transaction lock applied through 2027-01-01. Package ready for external auditor review.'

**Steps:**

1. In BigCapital, generate and export as PDF the Trial Balance, Balance Sheet, Profit and Loss, Cash Flow Statement, Journal Sheet, General Ledger for the bank account 'Bank Account', A/R Aging Summary, A/P Aging Summary, and Sales Tax Liability Summary — all for the fiscal year date range 2026-01-01 to 2026-12-31. Record the specific numeric totals from each report (debits/credits, assets/liabilities/equity, revenue/expenses/net income, operating cash flow, receivables, payables). Verify the bank account closing balance of -$215,382.44.
2. Lock all transactions before 2027-01-01 in BigCapital and verify the locking status.
3. In Frappe HRMS, export the Employee Information report for company 'TechVista Solutions Pvt. Ltd.' to CSV and record the active employee count, review the Salary Register for March and record gross/deductions/net totals, check Income Tax Deductions and Provident Fund Deductions reports for payroll period '2026' and record totals, review leave balance liabilities for leave type 'Sick Leave', and verify no outstanding employee advances exceed $750.
4. In Twenty CRM, filter Won opportunities for the fiscal year 2026-01-01 to 2026-12-31 and record the total count and total revenue. Create a comprehensive audit preparation note titled 'Audit Preparation Package — FY 2026' that includes all specific numeric values captured from BigCapital, Frappe HRMS, and CRM. Create a task titled 'Submit audit package to external auditors — FY 2026' with due date 2027-03-15.

**Login Credentials:**

- bigcapital: admin@bigcapital.local / admin123
- frappe-hrms: Administrator / admin
- twenty: phil.schiler@apple.dev / tim@apple.dev
