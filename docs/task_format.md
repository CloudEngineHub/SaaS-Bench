# Task Format

Each task lives in a directory under `tasks/<MODAL>/<DOMAIN>/<task_id>/` and contains
exactly three files:

```
tasks/
└── multi/uni-m
    └── Business/
        └── business_023/
            ├── description.md   # Human-readable task spec
            ├── meta.json        # Machine-readable metadata
            └── verify.py        # Scoring script
```

## description.md

Free-form Markdown shown to the agent as part of the user prompt. The
recommended structure:

```markdown
**Task Requirements:**
<one-paragraph problem statement>

**Steps:**
1. Open the Sales module.
2. ...

**Login Credentials:**
- Mattermost  →  user@example.com / Test1234!
```

The `**Steps:**` section is parsed by `saas_bench/loader.py` to pre-fill the
agent's `todo.md`. Steps must be a top-level numbered list ("1. ...").

## meta.json

```json
{
  "task_id": "business_023",
  "category_id": "Business",
  "meta_data": {
    "sites": ["hrms", "bigcapital", "twenty"],
    "require_login": true
  }
}
```

| Field                       | Required | Meaning                                       |
| --------------------------- | -------- | --------------------------------------------- |
| `task_id`                   | yes      | Globally unique id; matches the directory     |
| `category_id`               | yes      | Domain bucket; matches the parent directory   |
| `meta_data.sites`           | yes      | List of app keys from `saas_bench/apps.yaml`  |
| `meta_data.require_login`   | no       | Hint for the agent; not enforced              |

The harness uses `sites` to:
1. Decide which docker containers to start for this task's slot.
2. Build the "Application Access URLs" prompt header with the per-slot ports.
3. Inject `<APP>_PORT` / `<APP>_CONTAINER` / `<APP>_DB_CONTAINER` env vars
   into `verify.py`.

Unknown app keys are ignored with a warning — they do **not** fail the task.

## verify.py

See [verify_protocol.md](./verify_protocol.md).

## Adding a new task

1. Pick a `category_id` (or create a new one) and a unique `task_id`.
2. Create `tasks/<MODAL>/<DOMAIN>/<task_id>/{description.md, meta.json, verify.py}`.
3. Smoke-test the verify script against a known-good agent run, or run it
   manually with the env vars set by hand.
4. Open a PR.

The loader rejects directories missing `description.md` or `meta.json`; a
missing `verify.py` produces `status=SKIP` (the agent still runs but no
score is computed).
