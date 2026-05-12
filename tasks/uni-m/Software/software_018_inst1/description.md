**Task Requirements:**

Run a security vulnerability audit targeting dependency CVEs across the todo-api and blog-engine projects. In code-server, open the File Explorer, navigate into each project, and open todo-api/requirements.txt in todo-api and blog-engine/package.json in blog-engine in the editor; extract every dependency whose pinned version exactly matches one of the vulnerable entries in [{"library": "Flask", "version": "2.0.1"}, {"library": "Jinja2", "version": "3.0.1"}, {"library": "SQLAlchemy", "version": "1.4.22"}, {"library": "requests", "version": "2.25.1"}, {"library": "express", "version": "4.17.1"}, {"library": "ejs", "version": "3.1.6"}, {"library": "marked", "version": "2.0.0"}, {"library": "lodash", "version": "4.17.20"}]. In Baserow, create a database "Dependency Security Audit 2025Q1" with a table "CVE Registry" (fields: CVE ID [primary text], Project [single-select: todo-api/blog-engine], Library Name [text], Vulnerable Version [text], Fixed Version [text], CVSS Score [number with 1 decimal], Severity [single-select: Critical/High/Medium/Low], Discovered Date [date]).

**Steps:**

1. In code-server, open todo-api/requirements.txt and blog-engine/package.json and identify every dependency whose pinned version appears in [{"library": "Flask", "version": "2.0.1"}, {"library": "Jinja2", "version": "3.0.1"}, {"library": "SQLAlchemy", "version": "1.4.22"}, {"library": "requests", "version": "2.25.1"}, {"library": "express", "version": "4.17.1"}, {"library": "ejs", "version": "3.1.6"}, {"library": "marked", "version": "2.0.0"}, {"library": "lodash", "version": "4.17.20"}].
2. In Baserow, create database "Dependency Security Audit 2025Q1" and table "CVE Registry" with the exact schema specified (fields: CVE ID [primary text], Project [single-select: todo-api/blog-engine], Library Name [text], Vulnerable Version [text], Fixed Version [text], CVSS Score [number with 1 decimal], Severity [single-select: Critical/High/Medium/Low], Discovered Date [date]).

**Login Credentials:**

- code-server: (no username) / 8a128206e2177bce1e48e565
- baserow: admin@example.com / Admin1234
