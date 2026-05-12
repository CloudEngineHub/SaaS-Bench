**Task Requirements:**

Process a complete employee expense reimbursement cycle spanning HR expense claim approval, accounting expense recording and payment, and CRM documentation. In Frappe HRMS: (1) Navigate to the Expense Claim list and open the pending expense claim 'HR-EXP-2026-00006' submitted by employee 'Mohammed Farooq' (HR-EMP-00015). Verify it contains exactly three line items totaling ₹10,350.00. The line items are: 'Travel' for ₹8,500.00, 'Food' for ₹1,500.00, and 'Calls' for ₹350.00. (2) Approve the expense claim. (3) Navigate to the Unpaid Expense Claim report and verify that 'Mohammed Farooq' appears with an unpaid amount of ₹10,350.00 as an intermediate confirmation that approval succeeded. In BigCapital: (4) Create a vendor named 'Mohammed Farooq Reimbursement' with email 'mohammed.farooq@gmail.com'. (5) Ensure that three items exist in BigCapital corresponding to the expense types: 'Travel', 'Food', and 'Calls'. If any of these items do not already exist, create them as new items with the respective names. (6) Create a bill (purchase invoice) dated 2026-03-20 for vendor 'Mohammed Farooq Reimbursement' with three line entries referencing the items created/confirmed above: 'Travel' for ₹8,500.00, 'Food' for ₹1,500.00, and 'Calls' for ₹350.00. The bill total must equal ₹10,350.00. Approve (open) the bill. (7) Record a Payment Made dated 2026-04-05 against the bill for ₹10,350.00 from account 'Bank Account'. (8) Navigate to the A/P Aging Summary report filtered to as-of date 2026-04-05 and verify 'Mohammed Farooq Reimbursement' shows a zero balance (confirming the bill is fully paid). In Twenty CRM: (9) Create a task titled 'Expense reimbursement processed — Mohammed Farooq' with due date 2026-04-05 and body: 'Expense claim HR-EXP-2026-00006 approved and paid. Total: ₹10,350.00. Items: Travel (₹8,500.00), Food (₹1,500.00), Calls (₹350.00). Payment made from Bank Account on 2026-04-05.' Mark the task as complete.

**Steps:**

1. In Frappe HRMS, open expense claim 'HR-EXP-2026-00006' for 'Mohammed Farooq' (HR-EMP-00015) and verify it has exactly three line items totaling ₹10,350.00: 'Travel' (₹8,500.00), 'Food' (₹1,500.00), 'Calls' (₹350.00).
2. Approve the expense claim.
3. Navigate to the Unpaid Expense Claim report and confirm 'Mohammed Farooq' appears with unpaid amount ₹10,350.00 as an intermediate validation that the claim was approved correctly.
4. In BigCapital, create a vendor named 'Mohammed Farooq Reimbursement' with email 'mohammed.farooq@gmail.com'.
5. Ensure three items exist in BigCapital with names 'Travel', 'Food', and 'Calls'. If any item does not already exist, create it as a new item with the corresponding name.
6. Create a bill dated 2026-03-20 for vendor 'Mohammed Farooq Reimbursement' with three line entries referencing the items above: 'Travel' for ₹8,500.00, 'Food' for ₹1,500.00, 'Calls' for ₹350.00. The bill total must equal ₹10,350.00. Approve (open) the bill.
7. Record a Payment Made of ₹10,350.00 against the bill from 'Bank Account' dated 2026-04-05.
8. View the A/P Aging Summary as of 2026-04-05 and confirm 'Mohammed Farooq Reimbursement' has zero balance.
9. In Twenty CRM, create a task titled 'Expense reimbursement processed — Mohammed Farooq' with the full reimbursement details in the body, set due date to 2026-04-05, and mark the task as complete.

**Login Credentials:**

- frappe-hrms: Administrator / admin
- bigcapital: admin@bigcapital.local / admin123
- twenty: jane.austen@apple.dev / tim@apple.dev
