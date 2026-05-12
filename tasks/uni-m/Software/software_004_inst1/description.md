**Task Requirements:**

Plan a synchronized two-week sprint named "Sprint Synchronize 2025-W10" across two teams (Backend and Data) starting 2025-03-03 and ending 2025-03-17. In OpenProject project "Data Analytics Pipeline", create a Version named "Sprint Synchronize 2025-W10" with the specified start and end dates and status "open". Create exactly 4 work packages per team (prefix subjects with "[Backend]" or "[Data]"), each of type Feature, assigned to the version "Sprint Synchronize 2025-W10", with estimated time values summing to 32 for team A and 28 for team B. For exactly one work package in team A, add a "follows" relation to exactly one work package in team B to model the cross-team dependency. In code-server, open the todo-api project and add a single comment line "# Sprint Sprint Synchronize 2025-W10: integration touchpoint" at the top of todo-api/app.py and save. Create a Baserow database "Sprint Capacity Planner" with a table "Sprint Capacity" (fields: Team [primary text], Planned Hours [number], Work Package Count [number], Has Cross-Team Dep [boolean]) and add exactly two rows reflecting the counts and sums from OpenProject.

**Steps:**

1. In OpenProject "Data Analytics Pipeline", create the Version "Sprint Synchronize 2025-W10" with dates 2025-03-03 to 2025-03-17
2. Create 4 Feature work packages per team with the subject prefix convention, assign all to the version, and set estimated hours summing to the specified team totals
3. Add exactly one "follows" relation between a team A work package and a team B work package
4. In code-server, add the specified comment line at the top of todo-api/app.py and save
5. In Baserow, create "Sprint Capacity Planner" and the "Sprint Capacity" table, then populate two rows with the aggregated planned hours and work package counts

**Login Credentials:**

- openproject: admin / AdminPass123!
- code-server: (no username) / 8a128206e2177bce1e48e565
- baserow: admin@example.com / Admin1234
