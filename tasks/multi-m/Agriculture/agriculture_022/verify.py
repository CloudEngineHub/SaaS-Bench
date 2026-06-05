"""
Verifier for agriculture_022: Organic audit — cross-reference Grocy product
stock_id values (from the `stock` table, excluding `x%` placeholders) against
FarmOS harvest log `lot_number` attributes; flag discrepant products.

Checks: 8 weighted checks across grocy, farmos.
Strategy: grocy via docker exec sqlite3; farmos via JSON:API.

Required env vars:
  SERVER_HOSTNAME, GROCY_PORT, GROCY_CONTAINER, FARMOS_PORT, FARMOS_CONTAINER.
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

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

FARMOS_BASE = f"http://{HOST}:{FARMOS_PORT}"

GROCY_DB_CANDIDATES = ["/config/data/grocy.db", "/config/data/data/grocy.db", "/var/www/data/grocy.db"]

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


def farmos_api_get(path: str, timeout: int = 15) -> dict:
    url = f"{FARMOS_BASE}{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.api+json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"FarmOS API {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        raise RuntimeError(f"FarmOS API error: {e}")


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


def grocy_sql(query: str) -> str:
    db = _find_grocy_db()
    rc, stdout, stderr = docker_exec(
        GROCY_CONTAINER,
        "sqlite3", "-separator", "|", db, query,
        timeout=15,
    )
    if rc == 0:
        return stdout.strip()
    php_script = (
        f'$db = new PDO("sqlite:{db}");'
        f'$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);'
        f'$r = $db->query("{query.replace(chr(34), chr(92)+chr(34))}");'
        f'while($row=$r->fetch(PDO::FETCH_NUM))'
        f'{{ echo implode("|",$row)."\\n"; }}'
    )
    rc2, stdout2, stderr2 = docker_exec(
        GROCY_CONTAINER, "php", "-r", php_script, timeout=15,
    )
    if rc2 != 0:
        raise RuntimeError(f"grocy query failed: sqlite3({stderr.strip()}) php({stderr2.strip()})")
    return stdout2.strip()


# ── Data retrieval ────────────────────────────────────────────────────────────
def get_grocy_products_with_stock_ids() -> dict[int, dict]:
    """Return {product_id: {name, description, stock_ids: set}} for products with non-placeholder stock entries."""
    raw = grocy_sql(
        "SELECT p.id, p.name, COALESCE(p.description,''), s.stock_id "
        "FROM products p "
        "JOIN stock s ON s.product_id = p.id "
        "WHERE s.stock_id IS NOT NULL AND s.stock_id != '' "
        "AND s.stock_id NOT LIKE 'x%';"
    )
    products: dict[int, dict] = {}
    if not raw:
        return products
    for line in raw.split("\n"):
        parts = line.split("|", 3)
        if len(parts) >= 4:
            pid = int(parts[0].strip())
            stock_id = parts[3].strip()
            if pid not in products:
                products[pid] = {
                    "name": parts[1].strip(),
                    "description": parts[2].strip(),
                    "stock_ids": set(),
                }
            products[pid]["stock_ids"].add(stock_id)
    return products


def get_farmos_harvest_lot_numbers() -> set[str]:
    """Return set of lot_number values from FarmOS harvest logs via JSON:API."""
    lot_numbers: set[str] = set()
    path = "/api/log/harvest?page[limit]=50"
    while path:
        data = farmos_api_get(path)
        for item in data.get("data", []):
            lot = item.get("attributes", {}).get("lot_number")
            if lot and lot.strip():
                lot_numbers.add(lot.strip())
        next_link = data.get("links", {}).get("next")
        if next_link:
            href = next_link if isinstance(next_link, str) else next_link.get("href", "")
            if href and href.startswith(FARMOS_BASE):
                path = href[len(FARMOS_BASE):]
            elif href:
                path = href
            else:
                path = ""
        else:
            path = ""
    return lot_numbers


# ── Shared state (loaded once) ───────────────────────────────────────────────
grocy_products: dict[int, dict] = {}
farmos_lots: set[str] = set()
matched_pids: set[int] = set()
unmatched_pids: set[int] = set()


def load_data() -> None:
    global grocy_products, farmos_lots, matched_pids, unmatched_pids
    grocy_products = get_grocy_products_with_stock_ids()
    farmos_lots = get_farmos_harvest_lot_numbers()

    for pid, info in grocy_products.items():
        if info["stock_ids"] & farmos_lots:
            matched_pids.add(pid)
        else:
            unmatched_pids.add(pid)


# ── Individual checks ─────────────────────────────────────────────────────────
def check_1_grocy_has_products_with_batches() -> None:
    try:
        check("1. grocy_products_with_batches_exist", 1,
              len(grocy_products) > 0,
              f"found {len(grocy_products)} products with batch numbers"
              if grocy_products else "no products with batch numbers found in Grocy stock table")
    except Exception as e:
        check("1. grocy_products_with_batches_exist", 1, False, f"exception: {e}")


def check_2_farmos_has_harvest_logs() -> None:
    try:
        check("2. farmos_harvest_logs_exist", 1,
              len(farmos_lots) > 0,
              f"found {len(farmos_lots)} distinct lot numbers"
              if farmos_lots else "no harvest logs with lot numbers found in FarmOS")
    except Exception as e:
        check("2. farmos_harvest_logs_exist", 1, False, f"exception: {e}")


def check_3_matched_products_no_review_in_name() -> None:
    try:
        if not matched_pids:
            check("3. matched_no_review_in_name", 2, True, "no matched products to check")
            return
        bad = [grocy_products[pid] for pid in matched_pids
               if "[REVIEW REQUIRED]" in grocy_products[pid]["name"]]
        check("3. matched_no_review_in_name", 2,
              len(bad) == 0,
              f"{len(bad)} matched product(s) incorrectly flagged: "
              + ", ".join(f"'{p['name']}'" for p in bad[:3])
              if bad else f"all {len(matched_pids)} matched products are clean")
    except Exception as e:
        check("3. matched_no_review_in_name", 2, False, f"exception: {e}")


def check_4_matched_products_no_discrepancy_in_desc() -> None:
    try:
        if not matched_pids:
            check("4. matched_no_discrepancy_in_desc", 2, True, "no matched products to check")
            return
        bad = [grocy_products[pid] for pid in matched_pids
               if "DISCREPANCY" in grocy_products[pid]["description"].upper()]
        check("4. matched_no_discrepancy_in_desc", 2,
              len(bad) == 0,
              f"{len(bad)} matched product(s) incorrectly have DISCREPANCY: "
              + ", ".join(f"'{p['name']}'" for p in bad[:3])
              if bad else f"all {len(matched_pids)} matched products have clean descriptions")
    except Exception as e:
        check("4. matched_no_discrepancy_in_desc", 2, False, f"exception: {e}")


def check_5_unmatched_products_have_review_in_name() -> None:
    try:
        if not unmatched_pids:
            check("5. unmatched_have_review_in_name", 2, True, "no unmatched products to check")
            return
        missing = [grocy_products[pid] for pid in unmatched_pids
                   if "[REVIEW REQUIRED]" not in grocy_products[pid]["name"]]
        check("5. unmatched_have_review_in_name", 2,
              len(missing) == 0,
              f"{len(missing)}/{len(unmatched_pids)} unmatched product(s) missing [REVIEW REQUIRED]: "
              + ", ".join(f"'{p['name']}'" for p in missing[:3])
              if missing else f"all {len(unmatched_pids)} unmatched products have [REVIEW REQUIRED]")
    except Exception as e:
        check("5. unmatched_have_review_in_name", 2, False, f"exception: {e}")


def check_6_unmatched_products_have_discrepancy_in_desc() -> None:
    try:
        if not unmatched_pids:
            check("6. unmatched_have_discrepancy_in_desc", 2, True, "no unmatched products to check")
            return
        missing = [grocy_products[pid] for pid in unmatched_pids
                   if "DISCREPANCY" not in grocy_products[pid]["description"].upper()]
        check("6. unmatched_have_discrepancy_in_desc", 2,
              len(missing) == 0,
              f"{len(missing)}/{len(unmatched_pids)} unmatched product(s) missing DISCREPANCY note: "
              + ", ".join(f"'{p['name']}'" for p in missing[:3])
              if missing else f"all {len(unmatched_pids)} unmatched products have DISCREPANCY note")
    except Exception as e:
        check("6. unmatched_have_discrepancy_in_desc", 2, False, f"exception: {e}")


def check_7_discrepancy_note_exact_text() -> None:
    try:
        if not unmatched_pids:
            check("7. discrepancy_exact_text", 1, True, "no unmatched products to check")
            return
        exact_phrase = "DISCREPANCY: No matching FarmOS harvest log found"
        missing = [grocy_products[pid] for pid in unmatched_pids
                   if exact_phrase not in grocy_products[pid]["description"]]
        check("7. discrepancy_exact_text", 1,
              len(missing) == 0,
              f"{len(missing)}/{len(unmatched_pids)} missing exact phrase: "
              + ", ".join(f"'{p['name']}'" for p in missing[:3])
              if missing else f"all {len(unmatched_pids)} have exact discrepancy text")
    except Exception as e:
        check("7. discrepancy_exact_text", 1, False, f"exception: {e}")


def check_8_cross_app_consistency() -> None:
    try:
        if not grocy_products:
            check("8. cross_app_consistency", 3, False, "no grocy products with batches found")
            return

        errors = []
        for pid, info in grocy_products.items():
            has_match = pid in matched_pids
            has_review = "[REVIEW REQUIRED]" in info["name"]
            has_discrepancy = "DISCREPANCY" in info["description"].upper()

            if has_match and (has_review or has_discrepancy):
                errors.append(
                    f"'{info['name']}' matched in FarmOS but incorrectly flagged"
                )
            elif not has_match and (not has_review or not has_discrepancy):
                missing_parts = []
                if not has_review:
                    missing_parts.append("[REVIEW REQUIRED]")
                if not has_discrepancy:
                    missing_parts.append("DISCREPANCY")
                errors.append(
                    f"'{info['name']}' not in FarmOS but missing: "
                    + ", ".join(missing_parts)
                )

        check("8. cross_app_consistency", 3,
              len(errors) == 0,
              f"{len(errors)} error(s): " + "; ".join(errors[:3])
              if errors else f"all {len(grocy_products)} products correctly partitioned")
    except Exception as e:
        check("8. cross_app_consistency", 3, False, f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    load_data()

    check_1_grocy_has_products_with_batches()
    check_2_farmos_has_harvest_logs()
    check_3_matched_products_no_review_in_name()
    check_4_matched_products_no_discrepancy_in_desc()
    check_5_unmatched_products_have_review_in_name()
    check_6_unmatched_products_have_discrepancy_in_desc()
    check_7_discrepancy_note_exact_text()
    check_8_cross_app_consistency()

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
