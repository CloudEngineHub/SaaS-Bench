"""Run each task's verify.py, parse the results, and write them to JSON files.

verify.py output convention (all written to stderr):
  [PASS] ({n}pt) label  (details)
  [FAIL] ({n}pt) label  (details)
  SCORE: {score:.3f}  PASS: {all_pass}  ({earned}/{total})

run_verify must be called while the containers are still alive.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# -- SITE_CONFIG --------------------------------------------------------------
# Per-app env-var configuration.
#
# container_suffix / db_suffix:
#   prefix = f"rollout_{slot_id}_{app_name}"
#   app_container = prefix  (when suffix is an empty string)
#   app_container = prefix + suffix  (when suffix is non-empty)
#   db_var = None means do not set the DB_CONTAINER env var

SITE_CONFIG: dict[str, dict] = {
    "code-server": {
        "port_var":          "CODE_SERVER_PORT",
        "container_var":     "CODE_SERVER_CONTAINER",
        "container_suffix":  "",
        "db_var":            None,
        "db_suffix":         None,
    },
    "openproject": {
        "port_var":          "OPENPROJECT_PORT",
        "container_var":     "OPENPROJECT_CONTAINER",
        "container_suffix":  "",
        "db_var":            "OPENPROJECT_DB_CONTAINER",
        "db_suffix":         "",
    },
    "metabase": {
        "port_var":          "METABASE_PORT",
        "container_var":     "METABASE_CONTAINER",
        "container_suffix":  "",
        "db_var":            "METABASE_DB_CONTAINER",
        "db_suffix":         "",
    },
    "baserow": {
        "port_var":          "BASEROW_PORT",
        "container_var":     "BASEROW_CONTAINER",
        "container_suffix":  "",
        "db_var":            "BASEROW_DB_CONTAINER",
        "db_suffix":         "",
    },
    "twenty": {
        "port_var":          "TWENTY_PORT",
        "container_var":     "TWENTY_CONTAINER",
        "container_suffix":  "",
        "db_var":            "TWENTY_DB_CONTAINER",
        "db_suffix":         "",
    },
    "bigcapital": {
        "port_var":          "BIGCAPITAL_PORT",
        "container_var":     "BIGCAPITAL_CONTAINER",
        "container_suffix":  "",
        "db_var":            "BIGCAPITAL_DB_CONTAINER",
        "db_suffix":         "",
    },
    "hrms": {
        "port_var":          "HRMS_PORT",
        "container_var":     "HRMS_CONTAINER",
        "container_suffix":  "",
        "db_var":            "HRMS_DB_CONTAINER",
        "db_suffix":         "",
    },
    "pretix": {
        "port_var":          "PRETIX_PORT",
        "container_var":     "PRETIX_CONTAINER",
        "container_suffix":  "",
        "db_var":            "PRETIX_DB_CONTAINER",
        "db_suffix":         "",
    },
    "openemr": {
        "port_var":          "OPENEMR_PORT",
        "container_var":     "OPENEMR_CONTAINER",
        "container_suffix":  "",
        "db_var":            "OPENEMR_DB_CONTAINER",
        "db_suffix":         "",
    },
    "opnform": {
        "port_var":          "OPNFORM_PORT",
        "container_var":     "OPNFORM_CONTAINER",
        "container_suffix":  "",
        "db_var":            None,
        "db_suffix":         None,
    },
    # compose-based apps — app/db container names carry suffixes
    "onlyoffice": {
        "port_var":          "ONLYOFFICE_PORT",
        "container_var":     "ONLYOFFICE_CONTAINER",
        "container_suffix":  "-community",
        "db_var":            "ONLYOFFICE_DB_CONTAINER",
        "db_suffix":         "-mysql",
    },
    "mattermost": {
        "port_var":          "MATTERMOST_PORT",
        "container_var":     "MATTERMOST_CONTAINER",
        "container_suffix":  "",
        "db_var":            "MATTERMOST_DB_CONTAINER",
        "db_suffix":         "-postgres",
    },
    "owncloud": {
        "port_var":          "OWNCLOUD_PORT",
        "container_var":     "OWNCLOUD_CONTAINER",
        "container_suffix":  "",
        "db_var":            "OWNCLOUD_DB_CONTAINER",
        "db_suffix":         "-mariadb",
    },
    "roundcubemail": {
        "port_var":          "ROUNDCUBEMAIL_PORT",
        "container_var":     "ROUNDCUBEMAIL_CONTAINER",
        "container_suffix":  "",
        "db_var":            "ROUNDCUBEMAIL_DB_CONTAINER",
        "db_suffix":         "",
    },
    # -- AASC / IMC New Apps --------------------------------------------------
    "grocy": {
        "port_var":          "GROCY_PORT",
        "container_var":     "GROCY_CONTAINER",
        "container_suffix":  "",
        "db_var":            None,
        "db_suffix":         None,
    },
    "recipya": {
        "port_var":          "RECIPYA_PORT",
        "container_var":     "RECIPYA_CONTAINER",
        "container_suffix":  "",
        "db_var":            None,
        "db_suffix":         None,
    },
    "farmos": {
        "port_var":          "FARMOS_PORT",
        "container_var":     "FARMOS_CONTAINER",
        "container_suffix":  "",
        "db_var":            None,
        "db_suffix":         None,
    },
    "e-label": {
        "port_var":          "E_LABEL_PORT",
        "container_var":     "E_LABEL_CONTAINER",
        "container_suffix":  "",
        "db_var":            "E_LABEL_DB_CONTAINER",
        "db_suffix":         "",
    },
    "siyuan": {
        "port_var":          "SIYUAN_PORT",
        "container_var":     "SIYUAN_CONTAINER",
        "container_suffix":  "",
        "db_var":            None,
        "db_suffix":         None,
    },
    "watcharr": {
        "port_var":          "WATCHARR_PORT",
        "container_var":     "WATCHARR_CONTAINER",
        "container_suffix":  "",
        "db_var":            None,
        "db_suffix":         None,
    },
    "booklore": {
        "port_var":          "BOOKLORE_PORT",
        "container_var":     "BOOKLORE_CONTAINER",
        "container_suffix":  "",
        "db_var":            None,
        "db_suffix":         None,
    },
    "mediacms": {
        "port_var":          "MEDIACMS_PORT",
        "container_var":     "MEDIACMS_CONTAINER",
        "container_suffix":  "",
        "db_var":            None,
        "db_suffix":         None,
    },
    "photoprism": {
        "port_var":          "PHOTOPRISM_PORT",
        "container_var":     "PHOTOPRISM_CONTAINER",
        "container_suffix":  "",
        "db_var":            None,
        "db_suffix":         None,
    },
}


_SLOT_PREFIX = os.environ.get("SAAS_SLOT_PREFIX", "rollout")


def build_verify_env(
    task: dict,
    slot_id: int,
    port_map: dict[str, int],
    hostname: str,
) -> dict[str, str]:
    """Build the env dict required by verify.py (layered on top of the system env)."""
    env = os.environ.copy()
    env["SERVER_HOSTNAME"] = hostname

    # Allow verify.py files to use LLM_API_KEY/LLM_BASE_URL as a universal key source.
    if "MINDRA_API_KEY" not in env and env.get("LLM_API_KEY"):
        env["MINDRA_API_KEY"] = env["LLM_API_KEY"]
    if "MINDRA_BASE_URL" not in env and env.get("LLM_BASE_URL"):
        env["MINDRA_BASE_URL"] = env["LLM_BASE_URL"]

    sites: list[str] = task.get("meta", {}).get("meta_data", {}).get("sites", [])

    for site in sites:
        cfg = SITE_CONFIG.get(site)
        if cfg is None:
            continue  # unknown app, skip

        prefix = f"{_SLOT_PREFIX}_{slot_id}_{site}"

        # port
        port = port_map.get(site)
        if port is not None:
            env[cfg["port_var"]] = str(port)

        # app container
        app_container = prefix + cfg["container_suffix"]
        env[cfg["container_var"]] = app_container

        # db container
        if cfg["db_var"] is not None:
            db_container = prefix + cfg["db_suffix"]
            env[cfg["db_var"]] = db_container

    return env


# -- Output parsing -----------------------------------------------------------
_CHECK_RE = re.compile(
    r"^\[(PASS|FAIL)\]\s+\((\d+)pt\)\s+(.+?)(?:\s{2,}\((.+)\))?\s*$"
)
_SCORE_RE = re.compile(
    r"^SCORE:\s*([\d.]+)\s+PASS:\s*(True|False)\s+\((\d+)/(\d+)\)"
)


def _parse_verify_output(stderr_text: str) -> dict:
    checks = []
    score = 0.0
    earned = 0
    total = 0
    all_pass = False
    score_found = False

    for line in stderr_text.splitlines():
        line = line.strip()
        m = _CHECK_RE.match(line)
        if m:
            status, weight, label, detail = m.groups()
            checks.append({
                "label":  label.strip(),
                "weight": int(weight),
                "passed": status == "PASS",
                "detail": detail.strip() if detail else "",
            })
            continue
        m = _SCORE_RE.match(line)
        if m:
            score      = float(m.group(1))
            all_pass   = m.group(2) == "True"
            earned     = int(m.group(3))
            total      = int(m.group(4))
            score_found = True

    if not score_found and checks:
        total  = sum(c["weight"] for c in checks)
        earned = sum(c["weight"] for c in checks if c["passed"])
        score  = earned / total if total else 0.0
        all_pass = all(c["passed"] for c in checks)

    return {
        "checks":   checks,
        "score":    score,
        "earned":   earned,
        "total":    total,
        "all_pass": all_pass,
    }


# -- Main entry point ---------------------------------------------------------

def run_verify(
    task: dict,
    slot_id: int,
    port_map: dict[str, int],
    hostname: str,
    result_dir: str,
    run_suffix: str = "",
) -> dict:
    """Run verify.py, return the result dict, and write it to {task_id}{run_suffix}_verify.json.

    The path to verify.py is taken from task["verify_py_path"].
    Returns status=SKIP when verify.py is missing.
    """
    task_id      = task["task_id"]
    verify_path  = task.get("verify_py_path")
    out_path     = Path(result_dir) / f"{task_id}{run_suffix}_verify.json"

    def _save(result: dict) -> dict:
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    if not verify_path or not Path(verify_path).exists():
        return _save({"task_id": task_id, "status": "SKIP", "score": 0.0,
                      "checks": [], "error": "no verify.py"})

    env = build_verify_env(task, slot_id, port_map, hostname)

    try:
        proc = subprocess.run(
            [sys.executable, verify_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return _save({"task_id": task_id, "status": "ERROR", "score": 0.0,
                      "checks": [], "error": "timeout after 300s"})
    except Exception as e:
        return _save({"task_id": task_id, "status": "ERROR", "score": 0.0,
                      "checks": [], "error": str(e)})

    parsed = _parse_verify_output(proc.stderr)
    status = "PASS" if parsed["all_pass"] else ("FAIL" if parsed["checks"] else "ERROR")
    result = {
        "task_id":  task_id,
        "status":   status,
        "score":    parsed["score"],
        "earned":   parsed["earned"],
        "total":    parsed["total"],
        "all_pass": parsed["all_pass"],
        "checks":   parsed["checks"],
        "returncode": proc.returncode,
        "error":    None,
    }
    return _save(result)
