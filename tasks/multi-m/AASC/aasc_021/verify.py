"""
Verifier for aasc_021: Organic audit — cross-reference Grocy product batch numbers
against FarmOS harvest logs; flag unmatched products.

Checks: 8 weighted checks (14 total points) across grocy, farmos.
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
_grocy_products_with_batch: list[dict] = []
_farmos_harvest_names: set[str] = set()


def _load_grocy_products() -> list[dict]:
    global _grocy_products_with_batch
    if _grocy_products_with_batch:
        return _grocy_products_with_batch

    rows = grocy_sql_json(
        "SELECT p.id, p.name, p.description, ufv.value AS batch_number "
        "FROM products p "
        "JOIN userfield_values ufv ON ufv.object_id = p.id "
        "JOIN userfields uf ON uf.id = ufv.field_id "
        "WHERE uf.entity = 'products' "
        "AND uf.name = 'batch_number' "
        "AND ufv.value IS NOT NULL "
        "AND TRIM(ufv.value) != ''"
    )
    _grocy_products_with_batch = rows
    return rows


def _load_farmos_harvest_names() -> set[str]:
    global _farmos_harvest_names
    if _farmos_harvest_names:
        return _farmos_harvest_names

    rows = farmos_sql_json(
        "SELECT name FROM log_field_data WHERE type = 'harvest'"
    )
    _farmos_harvest_names = {r["name"].strip() for r in rows if r.get("name")}
    return _farmos_harvest_names


# ── Individual checks ─────────────────────────────────────────────────────────
def check_1_grocy_batch_products_retrievable() -> None:
    try:
        products = _load_grocy_products()
        check("1. grocy_batch_products_retrievable", 1, True,
              f"found {len(products)} products with batch_number userfield")
    except Exception as e:
        check("1. grocy_batch_products_retrievable", 1, False, f"exception: {e}")


def check_2_farmos_harvest_logs_retrievable() -> None:
    try:
        names = _load_farmos_harvest_names()
        check("2. farmos_harvest_logs_retrievable", 1, True,
              f"found {len(names)} harvest log names")
    except Exception as e:
        check("2. farmos_harvest_logs_retrievable", 1, False, f"exception: {e}")


def check_3_at_least_one_batch_product() -> None:
    try:
        products = _load_grocy_products()
        check("3. at_least_one_batch_product", 1, len(products) > 0,
              f"count={len(products)}" if products else "no products with batch_number found")
    except Exception as e:
        check("3. at_least_one_batch_product", 1, False, f"exception: {e}")


def check_4_at_least_one_harvest_log() -> None:
    try:
        names = _load_farmos_harvest_names()
        check("4. at_least_one_harvest_log", 1, len(names) > 0,
              f"count={len(names)}" if names else "no harvest logs found in farmos")
    except Exception as e:
        check("4. at_least_one_harvest_log", 1, False, f"exception: {e}")


def check_5_unmatched_products_flagged() -> None:
    try:
        products = _load_grocy_products()
        harvest_names = _load_farmos_harvest_names()

        unmatched = [
            p for p in products
            if p["batch_number"].strip() not in harvest_names
        ]

        if not unmatched:
            check("5. unmatched_products_flagged", 3, True,
                  "no unmatched products to flag")
            return

        missing_flag = []
        for p in unmatched:
            desc = p.get("description") or ""
            if AUDIT_FLAG not in desc:
                missing_flag.append(f"{p['name']} (batch={p['batch_number']})")

        if missing_flag:
            check("5. unmatched_products_flagged", 3, False,
                  f"{len(missing_flag)} unmatched products lack flag: "
                  + "; ".join(missing_flag[:5]))
        else:
            check("5. unmatched_products_flagged", 3, True,
                  f"all {len(unmatched)} unmatched products correctly flagged")
    except Exception as e:
        check("5. unmatched_products_flagged", 3, False, f"exception: {e}")


def check_6_matched_products_not_flagged() -> None:
    try:
        products = _load_grocy_products()
        harvest_names = _load_farmos_harvest_names()

        matched = [
            p for p in products
            if p["batch_number"].strip() in harvest_names
        ]

        if not matched:
            check("6. matched_products_not_flagged", 3, True,
                  "no matched products to verify")
            return

        wrongly_flagged = []
        for p in matched:
            desc = p.get("description") or ""
            if AUDIT_FLAG in desc:
                wrongly_flagged.append(f"{p['name']} (batch={p['batch_number']})")

        if wrongly_flagged:
            check("6. matched_products_not_flagged", 3, False,
                  f"{len(wrongly_flagged)} matched products wrongly flagged: "
                  + "; ".join(wrongly_flagged[:5]))
        else:
            check("6. matched_products_not_flagged", 3, True,
                  f"all {len(matched)} matched products correctly unflagged")
    except Exception as e:
        check("6. matched_products_not_flagged", 3, False, f"exception: {e}")


def check_7_flag_text_exact() -> None:
    try:
        products = _load_grocy_products()
        harvest_names = _load_farmos_harvest_names()

        unmatched = [
            p for p in products
            if p["batch_number"].strip() not in harvest_names
        ]

        if not unmatched:
            check("7. flag_text_exact", 2, True, "no unmatched products to verify flag text")
            return

        flagged = [p for p in unmatched if AUDIT_FLAG in (p.get("description") or "")]
        if not flagged:
            check("7. flag_text_exact", 2, False,
                  "no flagged products found to verify exact text")
            return

        bad = []
        for p in flagged:
            desc = p.get("description") or ""
            if AUDIT_FLAG in desc:
                idx = desc.index(AUDIT_FLAG)
                surrounding = desc[max(0, idx - 5):idx + len(AUDIT_FLAG) + 5]
                if AUDIT_FLAG not in surrounding:
                    bad.append(p["name"])
            else:
                bad.append(p["name"])

        check("7. flag_text_exact", 2, len(bad) == 0,
              f"all {len(flagged)} flagged products use exact flag text" if not bad
              else f"inexact flag in: {'; '.join(bad[:3])}")
    except Exception as e:
        check("7. flag_text_exact", 2, False, f"exception: {e}")


def check_8_both_matched_and_unmatched_exist() -> None:
    try:
        products = _load_grocy_products()
        harvest_names = _load_farmos_harvest_names()

        if not products:
            check("8. both_matched_and_unmatched_exist", 2, False,
                  "no products with batch_number")
            return

        matched_count = sum(
            1 for p in products
            if p["batch_number"].strip() in harvest_names
        )
        unmatched_count = len(products) - matched_count

        has_both = matched_count > 0 and unmatched_count > 0
        check("8. both_matched_and_unmatched_exist", 2, has_both,
              f"matched={matched_count}, unmatched={unmatched_count}"
              + ("" if has_both else " — expected both >0 for a meaningful audit"))
    except Exception as e:
        check("8. both_matched_and_unmatched_exist", 2, False, f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_1_grocy_batch_products_retrievable()
    check_2_farmos_harvest_logs_retrievable()
    check_3_at_least_one_batch_product()
    check_4_at_least_one_harvest_log()
    check_5_unmatched_products_flagged()
    check_6_matched_products_not_flagged()
    check_7_flag_text_exact()
    check_8_both_matched_and_unmatched_exist()

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
