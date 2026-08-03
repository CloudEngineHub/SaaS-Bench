"""
Verifier for agriculture_022: Organic audit — reconcile the warehouse's
delivery manifest (Grocy product -> batch number) against FarmOS harvest log
names; flag discrepant products with both a description note and a
'[REVIEW REQUIRED]' name suffix.

Checks: 7 weighted checks (13 total points) across grocy, farmos.
Strategy: grocy=docker exec PHP PDO (SQLite); farmos=docker exec PHP PDO (SQLite)

Required env vars:
  SERVER_HOSTNAME, GROCY_PORT, GROCY_CONTAINER, FARMOS_PORT, FARMOS_CONTAINER.
"""

import json
import os
import subprocess
import sys

# ── Config (from env) ─────────────────────────────────────────────────────────
HOST = os.getenv("SERVER_HOSTNAME", "localhost")

GROCY_PORT = os.getenv("GROCY_PORT")
GROCY_CONTAINER = os.getenv("GROCY_CONTAINER")
FARMOS_PORT = os.getenv("FARMOS_PORT")
FARMOS_CONTAINER = os.getenv("FARMOS_CONTAINER")

for _var_name, _var_val in [
    ("GROCY_PORT", GROCY_PORT),
    ("GROCY_CONTAINER", GROCY_CONTAINER),
    ("FARMOS_PORT", FARMOS_PORT),
    ("FARMOS_CONTAINER", FARMOS_CONTAINER),
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

DISCREPANCY_NOTE = "DISCREPANCY: No matching FarmOS harvest log found"
REVIEW_SUFFIX = "[REVIEW REQUIRED]"

# Delivery manifest from the task description: exact Grocy product name ->
# batch number. Matched entries reference FarmOS harvest logs that exist
# verbatim; unmatched entries reference harvest logs that do NOT exist.
MANIFEST_MATCHED = {
    "365 Everyday Value, Fat Free Skim Milk": "Cow Milk — Weekly Collection August Week 1",
    "Clover Honey": "2024 Honey Harvest — Hive A and B",
    "Pure Raw Honey": "2024 Honey Harvest — Hive A and B",
    "Black Forest Girl, Homemade Spaetzles, Egg Noodles": "2024 Egg Collection — Weekly Tally August Week 3",
}
MANIFEST_UNMATCHED = {
    "Nonfat Greek Yogurt": "2024 Goat Milk Collection — Weekly Tally September Week 1",
    "Cottage Cheese": "2024 Sheep Milk Collection — Weekly Tally August Week 3",
    "Kfactor 22 Manuka Honey": "2024 Manuka Honey Harvest — Hive C",
    "Monterey Jack Cheese": "2024 Cow Milk — Weekly Collection September Week 2",
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
    """Grocy products referenced by the manifest, keyed by base manifest name.

    Products whose name was appended with the review suffix no longer match
    by exact name; resolve them back to their base manifest name.
    """
    global _products_by_name
    if _products_by_name is not None:
        return _products_by_name
    names = list(MANIFEST_MATCHED) + list(MANIFEST_UNMATCHED)
    quoted = ", ".join("'" + n.replace("'", "''") + "'" for n in names)
    rows = grocy_sql_json(
        "SELECT id, name, COALESCE(description, '') AS description "
        f"FROM products WHERE name IN ({quoted})"
    )
    products = {r["name"]: r for r in rows}
    for base in names:
        if base in products:
            continue
        rows2 = grocy_sql_json(
            "SELECT id, name, COALESCE(description, '') AS description "
            "FROM products WHERE name LIKE "
            "'" + base.replace("'", "''") + "%" + REVIEW_SUFFIX + "%'"
        )
        if rows2:
            products[base] = rows2[0]
    _products_by_name = products
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


def _flagged_desc_names() -> set[str]:
    rows = grocy_sql_json(
        "SELECT name FROM products WHERE description LIKE "
        "'%" + DISCREPANCY_NOTE + "%'"
    )
    return {r["name"] for r in rows}


def _flagged_name_rows() -> list[dict]:
    return grocy_sql_json(
        "SELECT id, name FROM products WHERE name LIKE "
        "'%" + REVIEW_SUFFIX + "%'"
    )


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


def check_3_unmatched_have_review_suffix() -> None:
    """Every unmatched product's name ends with '[REVIEW REQUIRED]'."""
    try:
        products = _load_manifest_products()
        missing = []
        for name in MANIFEST_UNMATCHED:
            p = products.get(name)
            if p and REVIEW_SUFFIX in p["name"]:
                continue
            missing.append(name)
        check("3. unmatched_have_review_suffix", 2, not missing,
              f"all {len(MANIFEST_UNMATCHED)} unmatched products carry the suffix"
              if not missing
              else f"unmatched products missing suffix: {'; '.join(missing)}")
    except Exception as e:
        check("3. unmatched_have_review_suffix", 2, False, f"exception: {e}")


def check_4_unmatched_have_discrepancy_note() -> None:
    """Every unmatched product's description contains the exact discrepancy note."""
    try:
        products = _load_manifest_products()
        missing = []
        for name in MANIFEST_UNMATCHED:
            p = products.get(name)
            if not p:
                missing.append(f"{name} (product not found)")
            elif DISCREPANCY_NOTE not in (p.get("description") or ""):
                missing.append(name)
        check("4. unmatched_have_discrepancy_note", 3, not missing,
              f"all {len(MANIFEST_UNMATCHED)} unmatched products carry the note"
              if not missing
              else f"unmatched products missing note: {'; '.join(missing)}")
    except Exception as e:
        check("4. unmatched_have_discrepancy_note", 3, False, f"exception: {e}")


def check_5_matched_products_clean() -> None:
    """Matched products carry neither the name suffix nor a DISCREPANCY note.
    Requires audit evidence first (at least one unmatched product flagged)."""
    try:
        products = _load_manifest_products()
        evidence = [
            name for name in MANIFEST_UNMATCHED
            if products.get(name)
            and (REVIEW_SUFFIX in products[name].get("name", "")
                 or DISCREPANCY_NOTE in (products[name].get("description") or ""))
        ]
        if not evidence:
            check("5. matched_products_clean", 2, False,
                  "no audit evidence: no unmatched product has been flagged yet")
            return
        flagged_rows = _flagged_name_rows()
        flagged_suffix_ids = {int(r["id"]) for r in flagged_rows}
        desc_flagged = _flagged_desc_names()
        bad = []
        for name in MANIFEST_MATCHED:
            p = products.get(name)
            if not p:
                continue
            if int(p["id"]) in flagged_suffix_ids or REVIEW_SUFFIX in p["name"]:
                bad.append(f"{name} (name suffix)")
            if name in desc_flagged or "DISCREPANCY" in (p.get("description") or "").upper():
                bad.append(f"{name} (description)")
        check("5. matched_products_clean", 2, not bad,
              f"all {len(MANIFEST_MATCHED)} matched products are clean"
              if not bad else f"matched products wrongly flagged: {'; '.join(bad)}")
    except Exception as e:
        check("5. matched_products_clean", 2, False, f"exception: {e}")


def check_6_note_appended_not_replaced() -> None:
    """The discrepancy note is appended after the existing description text,
    not used as a replacement for it."""
    try:
        products = _load_manifest_products()
        flagged = [
            (name, products[name]["description"])
            for name in MANIFEST_UNMATCHED
            if products.get(name) and DISCREPANCY_NOTE in (products[name].get("description") or "")
        ]
        if not flagged:
            check("6. note_appended_not_replaced", 1, False,
                  "no flagged products found to verify append position")
            return
        bad = [name for name, desc in flagged
               if desc.index(DISCREPANCY_NOTE) == 0]
        check("6. note_appended_not_replaced", 1, not bad,
              f"all {len(flagged)} flagged products keep their original text"
              if not bad
              else f"note replaces original description in: {'; '.join(bad)}")
    except Exception as e:
        check("6. note_appended_not_replaced", 1, False, f"exception: {e}")


def check_7_flag_targeting_exact() -> None:
    """Store-wide, the products carrying the name suffix and the products
    carrying the description note are both exactly the unmatched set."""
    try:
        expected = set(MANIFEST_UNMATCHED)
        suffix_rows = _flagged_name_rows()
        suffix_base = set()
        for r in suffix_rows:
            base = r["name"].replace(REVIEW_SUFFIX, "").strip()
            suffix_base.add(base)
        desc_flagged = {
            r["name"].replace(REVIEW_SUFFIX, "").strip()
            for r in grocy_sql_json(
                "SELECT name FROM products WHERE description LIKE "
                "'%" + DISCREPANCY_NOTE + "%'"
            )
        }

        if not suffix_rows and not desc_flagged:
            check("7. flag_targeting_exact", 2, False,
                  "no products flagged anywhere in grocy")
            return

        problems = []
        extra_suffix = sorted(suffix_base - expected)
        missing_suffix = sorted(expected - suffix_base)
        if extra_suffix:
            problems.append(f"unexpected name suffixes: {'; '.join(extra_suffix)}")
        if missing_suffix:
            problems.append(f"missing name suffixes: {'; '.join(missing_suffix)}")
        extra_desc = sorted(desc_flagged - expected)
        missing_desc = sorted(expected - desc_flagged)
        if extra_desc:
            problems.append(f"unexpected notes: {'; '.join(extra_desc)}")
        if missing_desc:
            problems.append(f"missing notes: {'; '.join(missing_desc)}")

        check("7. flag_targeting_exact", 2, not problems,
              f"name suffixes and notes both cover exactly the {len(expected)} unmatched products"
              if not problems else " — ".join(problems))
    except Exception as e:
        check("7. flag_targeting_exact", 2, False, f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_1_manifest_products_exist()
    check_2_farmos_logs_match_manifest()
    check_3_unmatched_have_review_suffix()
    check_4_unmatched_have_discrepancy_note()
    check_5_matched_products_clean()
    check_6_note_appended_not_replaced()
    check_7_flag_targeting_exact()

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
