"""
Verifier for agriculture_021: Cross-app batch audit — check the receiving
office's delivery manifest (Grocy product -> batch number) against FarmOS
harvest log names; flag products whose batch number matches no harvest log.

Checks: 6 weighted checks (12 total points) across grocy, farmos.
Strategy: grocy=docker exec PHP PDO (SQLite); farmos=docker exec PHP PDO (SQLite)

Required env vars:
  SERVER_HOSTNAME, FARMOS_PORT, FARMOS_CONTAINER, GROCY_PORT, GROCY_CONTAINER
"""

import json
import os
import subprocess
import sys

# ── Config (from env) ─────────────────────────────────────────────────────────
HOST = os.getenv("SERVER_HOSTNAME", "localhost")

FARMOS_PORT = os.getenv("FARMOS_PORT")
FARMOS_CONTAINER = os.getenv("FARMOS_CONTAINER")
GROCY_PORT = os.getenv("GROCY_PORT")
GROCY_CONTAINER = os.getenv("GROCY_CONTAINER")

for _var_name, _var_val in [
    ("FARMOS_PORT", FARMOS_PORT),
    ("FARMOS_CONTAINER", FARMOS_CONTAINER),
    ("GROCY_PORT", GROCY_PORT),
    ("GROCY_CONTAINER", GROCY_CONTAINER),
]:
    if not _var_val:
        print(f"FATAL: {_var_name} not set", file=sys.stderr)
        sys.exit(1)

FARMOS_SQLITE = "/opt/drupal/web/sites/default/files/.ht.sqlite"

GROCY_DB_CANDIDATES = [
    "/config/data/grocy.db",
    "/config/data/data/grocy.db",
    "/var/www/data/grocy.db",
]

AUDIT_FLAG = "AUDIT FLAG: Missing FarmOS harvest log"

# Delivery manifest from the task description: exact Grocy product name ->
# batch number. Matched entries reference FarmOS harvest logs that exist
# verbatim; unmatched entries reference harvest logs that do NOT exist.
MANIFEST_MATCHED = {
    "Sliced Beets": "2024 Beet Harvest — North Field Center Bed",
    "Strawberries": "2024 Strawberry Harvest — Peak Week June 15",
    "Whole Kernel Corn": "2024 Sweet Corn Harvest — South Field 1",
    "Cherry Tomatoes By Sainsburys": "2024 Cherry Tomato Harvest — North Field West Bed 1",
    "Organic Peas & Shoestring Carrots": "2024 Carrot Harvest — North Field Center Bed 1",
}
MANIFEST_UNMATCHED = {
    "Organic Green Beans": "2024 Green Bean Harvest — North Field East Bed 1",
    "Chestnut Mushrooms": "2024 Chestnut Mushroom Harvest — West Greenhouse 1",
    "Shreds Iceberg": "2024 Iceberg Lettuce Harvest — North Field East Bed 2",
}

# ── Result accumulator ────────────────────────────────────────────────────────
_checks: list[tuple[str, int, bool, str]] = []


def check(label: str, weight: int, passed: bool, detail: str = "") -> None:
    _checks.append((label, weight, passed, detail))
    status = "PASS" if passed else "FAIL"
    tail = f"  ({detail})" if detail else ""
    print(f"[{status}] ({weight}pt) {label}{tail}", file=sys.stderr)


# ── Helpers ───────────────────────────────────────────────────────────────────
def docker_exec(container: str, *args: str, timeout: int = 15) -> tuple[int, str, str]:
    r = subprocess.run(
        ["docker", "exec", container, *args],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.returncode, r.stdout, r.stderr


_grocy_db_path = ""


def _find_grocy_db() -> str:
    global _grocy_db_path
    if _grocy_db_path:
        return _grocy_db_path
    for path in GROCY_DB_CANDIDATES:
        rc, _, _ = docker_exec(GROCY_CONTAINER, "test", "-f", path)
        if rc == 0:
            _grocy_db_path = path
            return path
    _grocy_db_path = GROCY_DB_CANDIDATES[0]
    return _grocy_db_path


def grocy_sql_json(query: str) -> list[dict]:
    db = _find_grocy_db()
    php_script = (
        '$db = new PDO("sqlite:' + db + '");'
        '$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);'
        '$r = $db->query(' + json.dumps(query) + ');'
        '$rows = $r->fetchAll(PDO::FETCH_ASSOC);'
        'echo json_encode($rows);'
    )
    rc, stdout, stderr = docker_exec(
        GROCY_CONTAINER, "php", "-r", php_script, timeout=15,
    )
    if rc != 0:
        raise RuntimeError(f"grocy php error (rc={rc}): {stderr.strip()}")
    if not stdout.strip():
        return []
    return json.loads(stdout.strip())


def farmos_sql_json(query: str) -> list[dict]:
    php_script = (
        '$db = new PDO("sqlite:' + FARMOS_SQLITE + '");'
        '$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);'
        '$r = $db->query(' + json.dumps(query) + ');'
        '$rows = $r->fetchAll(PDO::FETCH_ASSOC);'
        'echo json_encode($rows);'
    )
    rc, stdout, stderr = docker_exec(
        FARMOS_CONTAINER, "php", "-r", php_script, timeout=15,
    )
    if rc != 0:
        raise RuntimeError(f"farmos php error (rc={rc}): {stderr.strip()}")
    if not stdout.strip():
        return []
    return json.loads(stdout.strip())


# ── Cached state ──────────────────────────────────────────────────────────────
_products_by_name: dict[str, dict] | None = None
_farmos_harvest_names: set[str] | None = None


def _load_manifest_products() -> dict[str, dict]:
    """Grocy products referenced by the manifest, keyed by exact name."""
    global _products_by_name
    if _products_by_name is not None:
        return _products_by_name
    names = list(MANIFEST_MATCHED) + list(MANIFEST_UNMATCHED)
    quoted = ", ".join("'" + n.replace("'", "''") + "'" for n in names)
    rows = grocy_sql_json(
        "SELECT id, name, COALESCE(description, '') AS description "
        f"FROM products WHERE name IN ({quoted})"
    )
    _products_by_name = {r["name"]: r for r in rows}
    return _products_by_name


def _load_farmos_harvest_names() -> set[str]:
    global _farmos_harvest_names
    if _farmos_harvest_names is not None:
        return _farmos_harvest_names
    rows = farmos_sql_json(
        "SELECT name FROM log_field_data WHERE type = 'harvest'"
    )
    _farmos_harvest_names = {r["name"].strip() for r in rows if r.get("name")}
    return _farmos_harvest_names


# ── Individual checks ─────────────────────────────────────────────────────────
def check_1_manifest_products_exist() -> None:
    """All 8 manifest products exist in Grocy (exact name)."""
    try:
        products = _load_manifest_products()
        missing = [n for n in list(MANIFEST_MATCHED) + list(MANIFEST_UNMATCHED)
                   if n not in products]
        check("1. manifest_products_exist", 1, not missing,
              f"found {len(products)}/8 manifest products" if not missing
              else f"missing products: {'; '.join(missing)}")
    except Exception as e:
        check("1. manifest_products_exist", 1, False, f"exception: {e}")


def check_2_farmos_logs_match_manifest() -> None:
    """FarmOS harvest logs are retrievable and consistent with the manifest:
    every matched batch number exists verbatim, no unmatched one does."""
    try:
        names = _load_farmos_harvest_names()
        if not names:
            check("2. farmos_logs_match_manifest", 1, False,
                  "no harvest logs found in farmos")
            return
        missing = [b for b in MANIFEST_MATCHED.values() if b not in names]
        unexpected = [b for b in MANIFEST_UNMATCHED.values() if b in names]
        problems = []
        if missing:
            problems.append(f"expected logs missing: {'; '.join(missing)}")
        if unexpected:
            problems.append(f"unexpected logs present: {'; '.join(unexpected)}")
        check("2. farmos_logs_match_manifest", 1, not problems,
              f"{len(names)} harvest logs; manifest references consistent"
              if not problems else " — ".join(problems))
    except Exception as e:
        check("2. farmos_logs_match_manifest", 1, False, f"exception: {e}")


def check_3_unmatched_products_flagged() -> None:
    """Every manifest product whose batch number has no FarmOS harvest log
    carries the exact audit flag in its description."""
    try:
        products = _load_manifest_products()
        missing_flag = []
        for name in MANIFEST_UNMATCHED:
            p = products.get(name)
            if not p:
                missing_flag.append(f"{name} (product not found)")
            elif AUDIT_FLAG not in p["description"]:
                missing_flag.append(name)
        check("3. unmatched_products_flagged", 4, not missing_flag,
              f"all {len(MANIFEST_UNMATCHED)} unmatched products flagged"
              if not missing_flag
              else f"unmatched products lacking flag: {'; '.join(missing_flag)}")
    except Exception as e:
        check("3. unmatched_products_flagged", 4, False, f"exception: {e}")


def check_4_matched_products_not_flagged() -> None:
    """Products whose batch number exists in FarmOS must NOT be flagged.
    Requires audit evidence first (at least one unmatched product flagged)."""
    try:
        products = _load_manifest_products()
        flagged_unmatched = [
            name for name in MANIFEST_UNMATCHED
            if products.get(name) and AUDIT_FLAG in products[name]["description"]
        ]
        if not flagged_unmatched:
            check("4. matched_products_not_flagged", 2, False,
                  "no audit evidence: no unmatched product has been flagged yet")
            return
        wrongly_flagged = [
            name for name in MANIFEST_MATCHED
            if products.get(name) and AUDIT_FLAG in products[name]["description"]
        ]
        check("4. matched_products_not_flagged", 2, not wrongly_flagged,
              f"all {len(MANIFEST_MATCHED)} matched products correctly unflagged"
              if not wrongly_flagged
              else f"matched products wrongly flagged: {'; '.join(wrongly_flagged)}")
    except Exception as e:
        check("4. matched_products_not_flagged", 2, False, f"exception: {e}")


def check_5_flag_appended_not_replaced() -> None:
    """The flag is appended after the existing description text, not used as
    a replacement for it."""
    try:
        products = _load_manifest_products()
        flagged = [
            (name, products[name]["description"])
            for name in MANIFEST_UNMATCHED
            if products.get(name) and AUDIT_FLAG in products[name]["description"]
        ]
        if not flagged:
            check("5. flag_appended_not_replaced", 2, False,
                  "no flagged products found to verify append position")
            return
        bad = [name for name, desc in flagged
               if desc.index(AUDIT_FLAG) == 0]
        check("5. flag_appended_not_replaced", 2, not bad,
              f"all {len(flagged)} flagged products keep their original text"
              if not bad
              else f"flag replaces original description in: {'; '.join(bad)}")
    except Exception as e:
        check("5. flag_appended_not_replaced", 2, False, f"exception: {e}")


def check_6_flag_targeting_exact() -> None:
    """Store-wide, exactly the unmatched manifest products carry the flag —
    no more, no fewer."""
    try:
        rows = grocy_sql_json(
            "SELECT name FROM products WHERE description LIKE "
            "'%" + AUDIT_FLAG + "%'"
        )
        flagged_names = {r["name"] for r in rows}
        if not flagged_names:
            check("6. flag_targeting_exact", 2, False,
                  "no products flagged anywhere in grocy")
            return
        expected = set(MANIFEST_UNMATCHED)
        extra = sorted(flagged_names - expected)
        missing = sorted(expected - flagged_names)
        problems = []
        if extra:
            problems.append(f"unexpected flags: {'; '.join(extra)}")
        if missing:
            problems.append(f"missing flags: {'; '.join(missing)}")
        check("6. flag_targeting_exact", 2, not problems,
              f"exactly the {len(expected)} unmatched products are flagged"
              if not problems else " — ".join(problems))
    except Exception as e:
        check("6. flag_targeting_exact", 2, False, f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_1_manifest_products_exist()
    check_2_farmos_logs_match_manifest()
    check_3_unmatched_products_flagged()
    check_4_matched_products_not_flagged()
    check_5_flag_appended_not_replaced()
    check_6_flag_targeting_exact()

    total = sum(w for _, w, _, _ in _checks)
    earned = sum(w for _, w, p, _ in _checks if p)
    all_pass = all(p for _, _, p, _ in _checks) and bool(_checks)
    score = (earned / total) if total else 0.0

    print(
        f"SCORE: {score:.3f}  PASS: {all_pass}  ({earned}/{total})",
        file=sys.stderr,
    )
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
