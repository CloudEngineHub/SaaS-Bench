**Task Requirements:**

Run a dependency upgrade campaign for library "typescript" across the projects ["tabler", "weather-dashboard", "todo-api", "blog-engine"]. In code-server, use the global Search panel (Ctrl+Shift+F) with regex enabled, scoped via 'files to include' to "tabler/**,weather-dashboard/**,todo-api/**,blog-engine/**", to locate every manifest file (requirements.txt or package.json) containing "typescript"; for each hit, open the file in the editor and record the project name, manifest path, and the current pinned version string. In Baserow, create a database "TypeScript Upgrade Campaign July 2026" with a table "Upgrade Inventory" (fields: Project [primary text], Manifest Path [text], Current Version [text], Target Version [text], Migration Complexity [single-select: Low/Medium/High], Status [single-select: Pending/InProgress/Done], Captured At [date]) and insert exactly one row per discovered project, in the alphabetical order of Project, with Current Version from the manifest, Target Version = "5.4.5", Migration Complexity from {"tabler": "High", "weather-dashboard": "Medium", "todo-api": "Low", "blog-engine": "Low"} (keyed by project name), Status = "Pending", Captured At = 2026-07-08. Then duplicate the default Grid view as "High Complexity" and add a filter Migration Complexity = High. In OpenProject project "Mobile App Redesign", create exactly one Epic-type parent work package with subject "Upgrade typescript to 5.4.5", priority Normal, description exactly "Campaign Date: 2026-07-08; Target: 5.4.5; Projects: <N>" where <N> is the count of rows inserted; then create one Task-type child work package under that Epic per Baserow row where Status = Pending, subject "[<Project>] Bump typescript <Current Version> → 5.4.5", assignee OpenProject Admin, priority High when Migration Complexity = High, else Normal.

**Steps:**

1. In code-server, use Search (Ctrl+Shift+F) scoped to tabler/**,weather-dashboard/**,todo-api/**,blog-engine/** with regex to find every manifest containing typescript, and record Project, Manifest Path, and Current Version for each hit.
2. In Baserow, create database TypeScript Upgrade Campaign July 2026 and table "Upgrade Inventory" with the specified schema; insert exactly one row per project in alphabetical order with Target Version=5.4.5, Migration Complexity from {"tabler": "High", "weather-dashboard": "Medium", "todo-api": "Low", "blog-engine": "Low"}, Status=Pending, Captured At=2026-07-08.
3. Duplicate the default grid view and name it "High Complexity"; add a filter Migration Complexity = High.
4. In OpenProject project Mobile App Redesign, create an Epic with subject "Upgrade typescript to 5.4.5" and description listing the campaign date, target, and project count.
5. Under that Epic, create one Task child per Baserow row where Status=Pending, with the specified subject, assignee OpenProject Admin, and priority High for High complexity rows, else Normal.

**Login Credentials:**

- code-server: (no username) / 8a128206e2177bce1e48e565
- baserow: admin@example.com / Admin1234
- openproject: admin / AdminPass123!
