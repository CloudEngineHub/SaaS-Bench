**Task Requirements:**

Execute a quarter-end operations review spanning CRM pipeline analysis in Twenty, financial statement generation and aged receivables tracking in BigCapital, HR attendance and expense verification in Frappe HRMS, and event ticket performance review in Pretix. The review covers the period 2026-07-01 to 2026-09-30.

In BigCapital (complete these steps first to derive overdue client names): (6) Navigate to the Profit and Loss Sheet filtered to date range 2026-07-01 to 2026-09-30 with accounting basis 'Accrual'. Export the report as PDF. Record total revenue as PL_REVENUE, total expenses as PL_EXPENSES, and net income as PL_NET_INCOME. (7) Navigate to the Balance Sheet filtered to as-of date 2026-09-30 with accounting basis 'Accrual'. Export the report as PDF. Record total assets as BS_ASSETS, total liabilities as BS_LIABILITIES, and total equity as BS_EQUITY. (8) Navigate to the A/R Aging Summary report filtered to as-of date 2026-09-30. Export the report as PDF. Record total outstanding receivables as AR_TOTAL. Identify every unique customer name with a non-zero balance in the 61-90 day or 90+ day aging buckets. Record these names exactly as they appear in the report -- this derived list is referred to as OVERDUE_CLIENTS throughout the remaining steps. (9) Navigate to the A/P Aging Summary report filtered to as-of date 2026-09-30. Export the report as PDF. Record total outstanding payables as AP_TOTAL. (10) Navigate to the Cash Flow Statement filtered to date range 2026-07-01 to 2026-09-30. Export the report as PDF. Record net cash from operating activities as CASH_OPS. (11) Navigate to the Sales by Items report filtered to date range 2026-07-01 to 2026-09-30. Export the report as PDF. Record the top-selling item by revenue as TOP_ITEM and its total as TOP_ITEM_REVENUE.

In Twenty CRM: (1) Navigate to the Opportunities list. Use the filter bar to add conditions for Stage = 'Won' and Close Date between 2026-07-01 and 2026-09-30 (if the exact date-range filter is not available, filter by Stage = 'Won' and then manually identify opportunities whose close date falls within the quarter). Sort by amount descending. Record the total count of Won deals and their summed revenue -- these are referred to as WON_COUNT and WON_REVENUE. (2) Use the filter bar to add conditions for Stage = 'Lost' and Close Date between 2026-07-01 and 2026-09-30 (apply the same filtering approach used in step 1). Record the count as LOST_COUNT. (3) Filter opportunities by stage 'SCREENING' (open pipeline). Sort by amount descending. Record the total count and summed amount as OPEN_COUNT and OPEN_PIPELINE. (4) For each unique client name in the OVERDUE_CLIENTS list derived from the BigCapital A/R Aging Summary, search for a matching company in the Twenty Companies list. If an exact match is found, open the company detail page and create a task linked to that company titled 'Follow up on overdue receivable -- [client name]' with due date 2026-10-15 and body: 'Overdue balance identified in Q3 aged receivables review. Contact accounts payable to arrange payment. Review deadline: 2026-10-15.' If no exact company match exists in Twenty, create an unlinked task (not associated with any company record) with the same title, due date, and body, substituting the client name exactly as it appears in the BigCapital A/R Aging Summary report. (5) Compute the win rate as WON_COUNT / (WON_COUNT + LOST_COUNT) * 100, rounded to one decimal place. If WON_COUNT + LOST_COUNT equals 0, use 'N/A' as the win rate. Create a note titled 'Q3 Pipeline Summary -- 2026-09-30' with body: 'Won deals: WON_COUNT, total revenue: WON_REVENUE USD
Lost deals: LOST_COUNT
Open pipeline (SCREENING): OPEN_COUNT deals, OPEN_PIPELINE USD
Win rate: [computed value]%
Overdue clients flagged: [comma-separated OVERDUE_CLIENTS list]
Follow-up tasks created with due date 2026-10-15'

In Frappe HRMS: (12) Navigate to the Monthly Attendance Sheet report for the month of September 2026. If a company filter is available, set it to 'TechVista Solutions Pvt. Ltd.'; otherwise use the default view. Traverse all pages of the report if paginated. Record the total number of employees listed as ATTENDANCE_HEADCOUNT. Identify any employees with more than 5 absent days by checking the Absent column totals for each employee row. Record their names as HIGH_ABSENCE_EMPLOYEES. If no employees exceed the threshold, record HIGH_ABSENCE_EMPLOYEES as 'None'. (13) Navigate to the Unpaid Expense Claim report. Traverse all pages if paginated. Record the total count of unpaid claims as UNPAID_CLAIMS_COUNT and total unpaid amount as UNPAID_CLAIMS_TOTAL by summing the amount column across all rows in the report. (14) Navigate to the Employee Leave Balance Summary report. If a leave type filter is available, set it to 'Sick Leave'. If the leave type filter is not available, scan the report output for rows or columns corresponding to 'Sick Leave'. If 'Sick Leave' appears in the report output (either as a filtered result or as a column/row label), record the total outstanding leave balance for that leave type across all listed employees as LEAVE_LIABILITY_DAYS. If 'Sick Leave' does not appear in the report output at all, record LEAVE_LIABILITY_DAYS as 'Not available'. (15) Navigate to the Employee Advance Summary report. Traverse all pages if paginated. Count advances with status 'Unpaid' or those showing unclaimed balances. Record the count as OPEN_ADVANCES_COUNT and the total unclaimed amount as OPEN_ADVANCES_TOTAL by summing the relevant amount column values across all matching rows.

In Pretix: (16) Navigate to the Event Dashboard for event 'Hamilton' under organizer 'broadway-group'. Record the total orders count as EVENT_ORDERS and total revenue as EVENT_REVENUE from the dashboard widgets. (17) Navigate to the Event Orders Overview page for 'Hamilton'. Use the orders list and its product/item breakdown columns to determine the revenue attributable to product 'Balcony' as PROD1_REVENUE and product 'Playbill Program' as PROD2_REVENUE. Also use the order status filter or status column to count orders by status: paid orders as PAID_ORDERS, pending orders as PENDING_ORDERS, and cancelled orders as CANCELLED_ORDERS.

In Twenty CRM: (18) Create a note titled 'Q3 Operations Review -- Complete -- 2026-09-30' with body:
'FINANCIAL SUMMARY (Accrual basis):
- P&L: Revenue PL_REVENUE, Expenses PL_EXPENSES, Net Income PL_NET_INCOME
- Balance Sheet: Assets BS_ASSETS, Liabilities BS_LIABILITIES, Equity BS_EQUITY
- Cash Flow from Ops: CASH_OPS
- A/R Outstanding: AR_TOTAL (overdue clients: [comma-separated OVERDUE_CLIENTS list])
- A/P Outstanding: AP_TOTAL
- Top item by sales: TOP_ITEM at TOP_ITEM_REVENUE

CRM PIPELINE:
- Won: WON_COUNT deals, WON_REVENUE USD
- Lost: LOST_COUNT deals
- Open (SCREENING): OPEN_COUNT deals, OPEN_PIPELINE USD
- Win rate: [computed value]%

HR METRICS:
- Headcount (September 2026): ATTENDANCE_HEADCOUNT
- High absence (>5 days): HIGH_ABSENCE_EMPLOYEES
- Unpaid expense claims: UNPAID_CLAIMS_COUNT totaling UNPAID_CLAIMS_TOTAL USD
- Leave liability (Sick Leave): LEAVE_LIABILITY_DAYS days
- Open advances: OPEN_ADVANCES_COUNT totaling OPEN_ADVANCES_TOTAL USD

EVENT PERFORMANCE (Hamilton):
- Total orders: EVENT_ORDERS, revenue: EVENT_REVENUE USD
- Balcony: PROD1_REVENUE USD
- Playbill Program: PROD2_REVENUE USD
- Paid: PAID_ORDERS, Pending: PENDING_ORDERS, Cancelled: CANCELLED_ORDERS'
(19) Create a task titled 'Present Q3 operations review to leadership' with due date 2026-10-22 and body: 'All financial statements exported as PDF. CRM pipeline, HR metrics, and event performance compiled. Overdue collection tasks assigned. Review note: Q3 Operations Review -- Complete -- 2026-09-30.'

**Steps:**

1. In BigCapital, generate and export as PDF: Profit and Loss Sheet, Balance Sheet, A/R Aging Summary, A/P Aging Summary, Cash Flow Statement, and Sales by Items report -- all filtered to the quarter date range 2026-07-01 to 2026-09-30 and accounting basis Accrual. Record key figures from each report. From the A/R Aging Summary, derive the list of unique overdue client names (customers with non-zero balances in the 61-90 day or 90+ day aging buckets) -- this OVERDUE_CLIENTS list is used in subsequent Twenty CRM steps.
2. In Twenty CRM, use the filter bar to add conditions for Stage = 'Won' and Close Date between 2026-07-01 and 2026-09-30, then filter by 'Lost' with the same date range, then by the open stage 'SCREENING', recording counts and totals for each. For each unique client name in the OVERDUE_CLIENTS list derived from BigCapital, search for a matching company in Twenty; if an exact match is found, create a linked follow-up task, otherwise create an unlinked task with the client name exactly as shown in the A/R Aging report. Create a pipeline summary note titled 'Q3 Pipeline Summary -- 2026-09-30' with win rate computed to one decimal place (or 'N/A' if no Won+Lost deals) and the derived overdue client names.
3. In Frappe HRMS, review the Monthly Attendance Sheet for September 2026 (applying company filter 'TechVista Solutions Pvt. Ltd.' if available), traversing all pages if paginated. Review the Unpaid Expense Claim report (traversing all pages and summing the amount column). Review the Employee Leave Balance Summary (applying leave type filter 'Sick Leave' if available, or scanning report output for 'Sick Leave'; recording 'Not available' if the leave type does not appear). Review the Employee Advance Summary (traversing all pages, counting and summing unpaid/unclaimed advances). Record headcount, high-absence employees exceeding 5 absent days, unpaid claims, leave liability, and open advances.
4. In Pretix, review the Event Dashboard for 'Hamilton' under organizer 'broadway-group' for total order count and revenue, then the Event Orders Overview for product-level revenue breakdown for 'Balcony' and 'Playbill Program' using the product/item columns and for order status counts using the status filter or column (paid, pending, cancelled).
5. In Twenty CRM, create a comprehensive operations review note titled 'Q3 Operations Review -- Complete -- 2026-09-30' consolidating all data from the four applications with win rate computed to one decimal place (or 'N/A'), including the derived overdue client names, and create a presentation task titled 'Present Q3 operations review to leadership' with due date 2026-10-22 and body referencing the completed review note.

**Login Credentials:**

- twenty: tim@apple.dev / tim@apple.dev
- bigcapital: admin@bigcapital.local / admin123
- frappe-hrms: Administrator / admin
- pretix: admin@localhost / admin
