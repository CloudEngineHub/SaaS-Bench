**Task Requirements:**

As an Admin Manager, identify superseded documents in file storage, archive them, update the team via messaging, and send formal change notifications: (1) In ownCloud, navigate to the existing folder 'doc/healthcare'. Locate the files Kima_w_Medical_Center_Nursing_Position_Description.docx, Inflammation_Protein_Results_Mann_Whitney_U_Test_Ratios_Sensitivity_Specificity.docx, MassHealth_Medicaid_CHIP_Section_1115_Demonstration_Waiver.docx (3 files). For each file, view its file details (size and modification date) and record them. Rename each file by prepending 'ARCHIVED_' to its current name (e.g., 'Kima_w_Medical_Center_Nursing_Position_Description.docx' becomes 'ARCHIVED_Kima_w_Medical_Center_Nursing_Position_Description.docx'). Create a new folder named 'Obsolete_Healthcare_2026H1' under 'doc/healthcare'. Move all renamed files into 'Obsolete_Healthcare_2026H1'. Add the tag 'obsolete' to each moved file. Create a new text file named 'ACTIVE_HEALTHCARE_DOCS.txt' in 'doc/healthcare' with content 'Current Active Healthcare Documents:
- Kima Medical Center Nursing Position Description v3 (doc/healthcare/nursing_position_v3.docx)
- Inflammation Protein Study Final Report 2026 (doc/healthcare/inflammation_protein_final_2026.docx)
- MassHealth 1115 Waiver Renewal 2026 (doc/healthcare/masshealth_1115_renewal_2026.docx)' listing the current active document names and their locations. (2) In OnlyOffice, create a new spreadsheet titled 'Healthcare_Archive_Register_2026H1' in Common Documents. In Sheet1, set headers in row 1: Original Filename (A1), Archived Filename (B1), Original Size (C1), Last Modified (D1), Archived Date (E1), Replacement Document (F1). Populate 3 rows (rows 2 through 4) with the data collected from ownCloud: original names, archived names with 'ARCHIVED_' prefix, file sizes, modification dates, today's date '2026-04-20', and the replacement document names nursing_position_v3.docx, inflammation_protein_final_2026.docx, masshealth_1115_renewal_2026.docx. Add a final row with 'Total Archived' in column A and a COUNTA formula in column B counting all archived filenames. Share the spreadsheet with user 'amit.singh' for editing. (3) In Mattermost, in the Product & Design team, navigate to the existing channel 'bug-triage'. Post a message 'Healthcare Archive Notice: The following superseded healthcare documents have been moved to the archive folder. Originals: Kima_w_Medical_Center_Nursing_Position_Description.docx, Inflammation_Protein_Results_Mann_Whitney_U_Test_Ratios_Sensitivity_Specificity.docx, MassHealth_Medicaid_CHIP_Section_1115_Demonstration_Waiver.docx. Replacements: nursing_position_v3.docx, inflammation_protein_final_2026.docx, masshealth_1115_renewal_2026.docx. Effective 2026-04-20.' listing all archived files and their replacements. Then use /header to set the channel header to 'Report and triage bugs. Healthcare document archive audit complete 2026-04-20. See ACTIVE_HEALTHCARE_DOCS.txt for current versions.'. Send a direct message to user 'admin' with text 'Please review and revoke any external sharing links associated with the archived healthcare files in doc/healthcare/Obsolete_Healthcare_2026H1. Appreciated.' requesting removal of any external sharing on the archived files. (4) In Roundcube, create a new sender identity with display name 'Admin Manager - Healthcare Records', email 'admin.healthcare@mail.local', organization 'Corporate Records Office', and set a plain text signature 'Admin Manager
Healthcare Records Control
Corporate Records Office
admin.healthcare@mail.local'. Compose an email using this identity to carlos.mendez@mail.local, rachel.goldberg@mail.local, tom.andersen@mail.local, amira.hassan@mail.local with subject 'Formal Notice: Healthcare Document Supersession Effective 2026-04-20' and body 'Dear Department Heads,

Please be advised that the following healthcare documents have been formally superseded and archived as of 2026-04-20:

1. Kima_w_Medical_Center_Nursing_Position_Description.docx -> replaced by nursing_position_v3.docx (effective 2026-04-20)
2. Inflammation_Protein_Results_Mann_Whitney_U_Test_Ratios_Sensitivity_Specificity.docx -> replaced by inflammation_protein_final_2026.docx (effective 2026-04-20)
3. MassHealth_Medicaid_CHIP_Section_1115_Demonstration_Waiver.docx -> replaced by masshealth_1115_renewal_2026.docx (effective 2026-04-20)

All archived originals are now stored in doc/healthcare/Obsolete_Healthcare_2026H1 with the ARCHIVED_ prefix. Please direct your teams to use the replacement documents only.

Regards,
Admin Manager' listing each superseded document, its replacement, and the effective date. Set message priority to Normal. Send the email. Then navigate to Settings > Folders and create a new mail folder named 'Healthcare_Archive_Notices'. Navigate to Sent, select the sent email, and move it to 'Healthcare_Archive_Notices'.

**Steps:**

1. In ownCloud, locate superseded files, record their details, rename with 'ARCHIVED_' prefix, move to a new archive folder, tag each file, and create an index file of current versions
2. In OnlyOffice, create an archive register spreadsheet documenting all archived files with their metadata and replacement documents, including a COUNTA formula, and share with the records manager
3. In Mattermost, post an archive notice in the operations channel listing changes, update the channel header, and send a DM to IT admin requesting permissions cleanup
4. In Roundcube, create a new sender identity, compose and send a formal change notification email to department heads, create a mail folder for archive notifications, and move the sent email into it

**Login Credentials:**

- owncloud: admin / admin
- onlyoffice: admin@onlyoffice.local / NewAdmin123!
- mattermost: admin / SeedAdmin1pass
- roundcubemail: james.whitfield@mail.local / User123!
