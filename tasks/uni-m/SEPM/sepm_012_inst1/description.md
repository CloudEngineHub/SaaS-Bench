**Task Requirements:**

Publish an API endpoint registry and deprecation tracker for the todo-api service. In code-server, open the todo-api project and use the Search panel (Ctrl+Shift+F) scoped to files="todo-api/**" with regex enabled to find every Flask route registration matching the pattern @(app|bp)\.route\(; record each endpoint's HTTP method, URL path, source file, and line number. In Baserow, create a database "TodoAPI Endpoint Governance" with a table "API Endpoint Registry" (fields: Endpoint ID [primary text, formatted EP-<NNN>], Method [single-select: GET/POST/PUT/PATCH/DELETE], Path [text], Source File [text], Line Number [number], Version [single-select: v1/v2/v3], Status [single-select: Active/Deprecated/Removed], Deprecation Date [date, nullable]). Insert exactly one row per discovered route ordered by Source File alphabetically then ascending Line Number, assigning Endpoint IDs EP-001, EP-002, ...; set Version from [["/api/v1/", "v1"], ["/api/v2/", "v2"], ["/api/v3/", "v3"], ["/health", "v1"]] (keyed by Path), Status=Active for all rows, Deprecation Date=null.

**Steps:**

1. In code-server, open the todo-api project; use the Search panel with regex and file scope "todo-api/**" to find route registrations matching @(app|bp)\.route\(; collect method, path, file, line number for each match
2. In Baserow, create database "TodoAPI Endpoint Governance" and the "API Endpoint Registry" table; insert one row per endpoint in the specified deterministic order with sequential Endpoint IDs and Version assignments from [["/api/v1/", "v1"], ["/api/v2/", "v2"], ["/api/v3/", "v3"], ["/health", "v1"]]

**Login Credentials:**

- code-server: (no username) / 8a128206e2177bce1e48e565
- baserow: admin@example.com / Admin1234
- openproject: admin / AdminPass123!
