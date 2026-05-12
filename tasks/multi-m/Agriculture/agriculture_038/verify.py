"""
Verifier for agriculture_038: Cross-app batch traceability audit (Grocy <-> FarmOS)

Checks: 10 weighted checks (18 pts total) across grocy, farmos.
Strategy: docker exec PHP/SQLite for both Grocy and FarmOS.

Required env vars:
  SERVER_HOSTNAME, GROCY_PORT, GROCY_CONTAINER, FARMOS_PORT, FARMOS_CONTAINER
"""

import os
import sys
import subprocess
import json
import base64

# ── Config (from env) ─────────────────────────────────────────────────────────
HOST = os.getenv("SERVER_HOSTNAME", "localhost")
GROCY_PORT = os.getenv("GROCY_PORT")
GROCY_CONTAINER = os.getenv("GROCY_CONTAINER")
FARMOS_PORT = os.getenv("FARMOS_PORT")
FARMOS_CONTAINER = os.getenv("FARMOS_CONTAINER")

for _var, _val in [
    ("GROCY_PORT", GROCY_PORT),
    ("GROCY_CONTAINER", GROCY_CONTAINER),
    ("FARMOS_PORT", FARMOS_PORT),
    ("FARMOS_CONTAINER", FARMOS_CONTAINER),
]:
    if not _val:
        print(f"FATAL: {_var} not set", file=sys.stderr)
        sys.exit(1)

GROCY_DB_PATH = "/config/data/grocy.db"
FARMOS_DB_PATH = "/opt/drupal/web/sites/default/files/.ht.sqlite"

DISCREPANCY_TEXT = "DISCREPANCY: No FarmOS Harvest Log"

# ── Result accumulator ────────────────────────────────────────────────────────
_checks: list[tuple[str, int, bool, str]] = []


def check(label: str, weight: int, passed: bool, detail: str = "") -> None:
    _checks.append((label, weight, passed, detail))
    status = "PASS" if passed else "FAIL"
    tail = f"  ({detail})" if detail else ""
    print(f"[{status}] ({weight}pt) {label}{tail}", file=sys.stderr)


# ── Helpers ───────────────────────────────────────────────────────────────────
def grocy_query(sql: str, timeout: int = 15) -> list[dict]:
    php_code = (
        '$pdo = new PDO("sqlite:' + GROCY_DB_PATH + '");'
        "$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);"
        "$stmt = $pdo->query(" + json.dumps(sql) + ");"
        "$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);"
        "echo json_encode($rows);"
    )
    r = subprocess.run(
        ["docker", "exec", GROCY_CONTAINER, "php", "-r", php_code],
        capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Grocy PHP query error: {r.stderr.strip()}")
    if not r.stdout.strip():
        return []
    return json.loads(r.stdout.strip())


def farmos_query(sql: str, timeout: int = 15) -> list[dict]:
    b64_sql = base64.b64encode(sql.encode()).decode()
    php_code = (
        "$sql = base64_decode('" + b64_sql + "');"
        "$db = new SQLite3('" + FARMOS_DB_PATH + "');"
        "$db->createCollation('NOCASE_UTF8', function($a,$b){return strnatcasecmp($a,$b);});"
        "$r = $db->query($sql);"
        "if (!$r) { echo '[]'; exit(0); }"
        "$rows = [];"
        "while ($row = $r->fetchArray(SQLITE3_ASSOC)) $rows[] = $row;"
        "echo json_encode($rows);"
    )
    r = subprocess.run(
        ["docker", "exec", FARMOS_CONTAINER, "php", "-r", php_code],
        capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError(f"FarmOS PHP query error: {r.stdout.strip()} {r.stderr.strip()}")
    if not r.stdout.strip():
        return []
    return json.loads(r.stdout.strip())


# ── Data fetchers ─────────────────────────────────────────────────────────────
def get_grocy_batch_products() -> list[dict]:
    """Get all Grocy products with a non-empty batch_number userfield."""
    sql = (
        "SELECT p.id AS product_id, p.name AS product_name, "
        "COALESCE(p.description, '') AS description, uv.value AS batch_number "
        "FROM products p "
        "JOIN userfield_values uv ON uv.object_id = CAST(p.id AS TEXT) "
        "JOIN userfields uf ON uf.id = uv.field_id "
        "WHERE uf.entity = 'products' AND uf.name = 'batch_number' "
        "AND uv.value IS NOT NULL AND uv.value != ''"
    )
    return grocy_query(sql)


def get_farmos_harvest_log_names() -> set[str]:
    """Get all FarmOS harvest log names as a set."""
    sql = (
        "SELECT name FROM log_field_data "
        "WHERE type = 'harvest' AND name IS NOT NULL AND name != ''"
    )
    rows = farmos_query(sql)
    return {r["name"] for r in rows}


# ── Individual checks ─────────────────────────────────────────────────────────
def check_1_batch_number_userfield_exists() -> None:
    """Grocy has a userfield named 'batch_number' on entity 'products'."""
    try:
        rows = grocy_query(
            "SELECT id, entity, name, caption FROM userfields "
            "WHERE entity = 'products' AND name = 'batch_number'"
        )
        check("1. batch_number_userfield_exists", 1, len(rows) > 0,
              f"found userfield id={rows[0]['id']}" if rows else "no batch_number userfield on products")
    except Exception as e:
        check("1. batch_number_userfield_exists", 1, False, f"exception: {e}")


def check_2_products_have_batch_numbers() -> None:
    """At least one Grocy product has a non-empty batch_number value."""
    try:
        products = get_grocy_batch_products()
        check("2. products_have_batch_numbers", 1, len(products) > 0,
              f"found {len(products)} products with batch_number" if products
              else "no products have batch_number values")
    except Exception as e:
        check("2. products_have_batch_numbers", 1, False, f"exception: {e}")


def check_3_farmos_harvest_logs_exist() -> None:
    """FarmOS has at least one harvest log."""
    try:
        names = get_farmos_harvest_log_names()
        check("3. farmos_harvest_logs_exist", 1, len(names) > 0,
              f"found {len(names)} harvest logs" if names else "no harvest logs in FarmOS")
    except Exception as e:
        check("3. farmos_harvest_logs_exist", 1, False, f"exception: {e}")


def check_4_matched_products_no_discrepancy() -> None:
    """Products whose batch_number matches a FarmOS harvest log do NOT have the discrepancy text."""
    try:
        products = get_grocy_batch_products()
        harvest_names = get_farmos_harvest_log_names()
        matched = [p for p in products if p["batch_number"] in harvest_names]
        false_flags = [
            f"{p['product_name']} (batch={p['batch_number']})"
            for p in matched if DISCREPANCY_TEXT in p.get("description", "")
        ]
        if not matched:
            check("4. matched_products_no_discrepancy", 2, False,
                  "vacuous: no matched products (precondition not met — no batch_number values or no harvest logs)")
        else:
            check("4. matched_products_no_discrepancy", 2, len(false_flags) == 0,
                  f"false flags: {', '.join(false_flags[:5])}" if false_flags else "no false flags")
    except Exception as e:
        check("4. matched_products_no_discrepancy", 2, False, f"exception: {e}")


def check_5_unmatched_products_have_discrepancy() -> None:
    """Unmatched products have 'DISCREPANCY: No FarmOS Harvest Log' in their description."""
    try:
        products = get_grocy_batch_products()
        harvest_names = get_farmos_harvest_log_names()
        unmatched = [p for p in products if p["batch_number"] not in harvest_names]
        missing_flag = [
            f"{p['product_name']} (batch={p['batch_number']})"
            for p in unmatched if DISCREPANCY_TEXT not in p.get("description", "")
        ]
        if not unmatched:
            check("5. unmatched_products_have_discrepancy", 3, False,
                  "vacuous: no unmatched products (precondition not met — no batch_number values to evaluate)")
        else:
            check("5. unmatched_products_have_discrepancy", 3, len(missing_flag) == 0,
                  f"missing discrepancy text: {', '.join(missing_flag[:5])}"
                  if missing_flag else f"all {len(unmatched)} unmatched products flagged")
    except Exception as e:
        check("5. unmatched_products_have_discrepancy", 3, False, f"exception: {e}")


def check_6_discrepancy_text_appended() -> None:
    """For flagged products, the discrepancy text is appended (not replacing the description)."""
    try:
        products = get_grocy_batch_products()
        harvest_names = get_farmos_harvest_log_names()
        unmatched_flagged = [
            p for p in products
            if p["batch_number"] not in harvest_names
            and DISCREPANCY_TEXT in p.get("description", "")
        ]
        if not unmatched_flagged:
            check("6. discrepancy_text_appended", 2, False,
                  "vacuous: no flagged products (agent did not write the discrepancy text)")
            return

        bad = []
        for p in unmatched_flagged:
            desc = p.get("description", "").strip()
            if desc == DISCREPANCY_TEXT:
                pass
            elif DISCREPANCY_TEXT not in desc:
                bad.append(f"{p['product_name']}: text missing")
            elif desc.startswith(DISCREPANCY_TEXT) and len(desc) > len(DISCREPANCY_TEXT):
                bad.append(f"{p['product_name']}: discrepancy at start, not appended")

        check("6. discrepancy_text_appended", 2, len(bad) == 0,
              "; ".join(bad[:3]) if bad else f"{len(unmatched_flagged)} products correctly appended")
    except Exception as e:
        check("6. discrepancy_text_appended", 2, False, f"exception: {e}")


def check_7_all_batch_products_checked() -> None:
    """Every product with a batch_number was either matched or flagged."""
    try:
        products = get_grocy_batch_products()
        harvest_names = get_farmos_harvest_log_names()
        unchecked = [
            f"{p['product_name']} (batch={p['batch_number']})"
            for p in products
            if p["batch_number"] not in harvest_names
            and DISCREPANCY_TEXT not in p.get("description", "")
        ]
        check("7. all_batch_products_checked", 2, len(unchecked) == 0,
              f"unchecked: {', '.join(unchecked[:5])}" if unchecked
              else f"all {len(products)} batch products accounted for")
    except Exception as e:
        check("7. all_batch_products_checked", 2, False, f"exception: {e}")


def check_8_no_false_positives() -> None:
    """No product WITHOUT a batch_number has the discrepancy text."""
    try:
        sql = (
            "SELECT p.id, p.name, COALESCE(p.description, '') AS description "
            "FROM products p "
            "WHERE p.id NOT IN ("
            "  SELECT CAST(uv.object_id AS INTEGER) FROM userfield_values uv "
            "  JOIN userfields uf ON uf.id = uv.field_id "
            "  WHERE uf.entity = 'products' AND uf.name = 'batch_number' "
            "  AND uv.value IS NOT NULL AND uv.value != ''"
            ") AND p.description LIKE '%" + DISCREPANCY_TEXT + "%'"
        )
        rows = grocy_query(sql)
        false_pos = [r["name"] for r in rows]
        check("8. no_false_positives", 2, len(false_pos) == 0,
              f"false positives: {', '.join(false_pos[:5])}" if false_pos
              else "no products without batch_number have discrepancy text")
    except Exception as e:
        check("8. no_false_positives", 2, False, f"exception: {e}")


def check_9_exact_match_used() -> None:
    """FarmOS harvest log name field exactly matches batch_number (not partial)."""
    try:
        products = get_grocy_batch_products()
        harvest_names = get_farmos_harvest_log_names()
        matched = [p for p in products if p["batch_number"] in harvest_names]
        if not matched:
            check("9. exact_match_used", 2, False,
                  "vacuous: no matched products to verify exact-match (precondition not met)")
            return

        bad = []
        for p in matched:
            bn = p["batch_number"]
            partial_only = [h for h in harvest_names if bn in h and h != bn]
            if partial_only and bn not in harvest_names:
                bad.append(f"{p['product_name']}: partial match only ({partial_only[0]})")

        check("9. exact_match_used", 2, len(bad) == 0,
              "; ".join(bad[:3]) if bad else f"{len(matched)} exact matches confirmed")
    except Exception as e:
        check("9. exact_match_used", 2, False, f"exception: {e}")


def check_10_discrepancy_count_correct() -> None:
    """Count of flagged products equals count of unmatched batch numbers."""
    try:
        products = get_grocy_batch_products()
        harvest_names = get_farmos_harvest_log_names()
        unmatched_count = sum(1 for p in products if p["batch_number"] not in harvest_names)

        flagged_sql = (
            "SELECT COUNT(*) AS cnt FROM products p "
            "JOIN userfield_values uv ON uv.object_id = CAST(p.id AS TEXT) "
            "JOIN userfields uf ON uf.id = uv.field_id "
            "WHERE uf.entity = 'products' AND uf.name = 'batch_number' "
            "AND uv.value IS NOT NULL AND uv.value != '' "
            "AND p.description LIKE '%" + DISCREPANCY_TEXT + "%'"
        )
        rows = grocy_query(flagged_sql)
        flagged_count = int(rows[0]["cnt"]) if rows else 0

        check("10. discrepancy_count_correct", 2, flagged_count == unmatched_count,
              f"unmatched={unmatched_count}, flagged={flagged_count}"
              if flagged_count != unmatched_count
              else f"both={unmatched_count}")
    except Exception as e:
        check("10. discrepancy_count_correct", 2, False, f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_1_batch_number_userfield_exists()
    check_2_products_have_batch_numbers()
    check_3_farmos_harvest_logs_exist()
    check_4_matched_products_no_discrepancy()
    check_5_unmatched_products_have_discrepancy()
    check_6_discrepancy_text_appended()
    check_7_all_batch_products_checked()
    check_8_no_false_positives()
    check_9_exact_match_used()
    check_10_discrepancy_count_correct()

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
