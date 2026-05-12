"""
Verifier for agriculture_003: Create Pinot Noir 2024 digital wine label in e-label

Checks: 11 weighted checks across e-label.
Strategy: docker exec MSSQL (sqlcmd) for all checks.

Required env vars:
  SERVER_HOSTNAME, E_LABEL_PORT, E_LABEL_CONTAINER
"""

import os
import sys
import subprocess

# ── Config (from env) ─────────────────────────────────────────────────────────
HOST = os.getenv("SERVER_HOSTNAME", "localhost")

E_LABEL_PORT = os.getenv("E_LABEL_PORT")
E_LABEL_CONTAINER = os.getenv("E_LABEL_CONTAINER")

_missing = []
for var in ["E_LABEL_PORT", "E_LABEL_CONTAINER"]:
    if not os.getenv(var):
        _missing.append(var)
if _missing:
    print(f"FATAL: {', '.join(_missing)} not set", file=sys.stderr)
    sys.exit(1)


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


def _find_db_container(app_container: str, env_var: str, fallback_names: list[str]) -> str:
    candidates = [
        os.getenv(env_var, ""),
        app_container + "-db",
    ]
    if "-" in app_container:
        candidates.append(app_container.rsplit("-", 1)[0] + "-db")
    candidates.extend(fallback_names)
    for name in [c for c in candidates if c]:
        try:
            rc, _, _ = docker_exec(name, "echo", "ok", timeout=5)
            if rc == 0:
                return name
        except Exception:
            continue
    return app_container + "-db"


E_LABEL_DB = _find_db_container(E_LABEL_CONTAINER, "E_LABEL_DB_CONTAINER", ["elabel-db", "elabel_db"])


def sqlcmd(query: str, timeout: int = 15) -> tuple[int, str, str]:
    for path in ["/opt/mssql-tools18/bin/sqlcmd", "/opt/mssql-tools/bin/sqlcmd"]:
        rc, stdout, stderr = docker_exec(
            E_LABEL_DB, path,
            "-S", "localhost", "-U", "sa", "-P", "Elabel2024!Strong",
            "-d", "elabel", "-C", "-h", "-1", "-s", "|", "-W",
            "-Q", query,
            timeout=timeout,
        )
        if rc == 0 or "not found" not in stderr.lower():
            return rc, stdout.strip(), stderr
    return rc, stdout.strip(), stderr


def _parse_sqlcmd_rows(stdout: str) -> list[list[str]]:
    rows = []
    for line in stdout.split("\n"):
        line = line.strip()
        if not line or "rows affected" in line.lower():
            continue
        rows.append([c.strip() for c in line.split("|")])
    return rows


# ── Shared state loaded once ────────────────────────────────────────────────
_product: dict = {}


def _load_product() -> bool:
    global _product
    query = (
        "SELECT TOP 1 "
        "  Name, FBOName, WineVintage, WineAppellation, WineAlcohol, Volume, "
        "  CAST(Id AS NVARCHAR(36)), Brand, WineType "
        "FROM Product "
        "WHERE ("
        "  Name LIKE '%Pinot Noir%' OR Name LIKE '%Estate Pinot%' "
        "  OR Brand LIKE '%Pinot Noir%' OR Brand LIKE '%Estate Pinot%' "
        "  OR FBOName LIKE '%Boutique Organic%' "
        ") "
        "ORDER BY CreatedOn DESC"
    )
    rc, stdout, _ = sqlcmd(query)
    rows = _parse_sqlcmd_rows(stdout) if rc == 0 else []
    if not rows:
        rc2, stdout2, _ = sqlcmd(
            "SELECT TOP 1 "
            "  Name, FBOName, WineVintage, WineAppellation, WineAlcohol, Volume, "
            "  CAST(Id AS NVARCHAR(36)), Brand, WineType "
            "FROM Product ORDER BY CreatedOn DESC"
        )
        rows = _parse_sqlcmd_rows(stdout2) if rc2 == 0 else []
    if rows and len(rows[0]) >= 7:
        r = rows[0]
        _product.update({
            "name": r[0], "fbo_name": r[1], "vintage": r[2],
            "appellation": r[3], "alcohol": r[4], "volume": r[5],
            "id": r[6], "brand": r[7] if len(r) > 7 else "",
            "wine_type": r[8] if len(r) > 8 else "",
        })
        return True
    return False


# ── Checks ────────────────────────────────────────────────────────────────────

def check_1_product_exists() -> None:
    found = _load_product()
    check("1. wine product exists", 1, found,
          f"name='{_product.get('name', '')}'" if found else "no matching product found")


def check_2_producer() -> None:
    fbo = _product.get("fbo_name", "")
    ok = fbo.lower().strip() == "boutique organic farm" if fbo and fbo.lower() not in ("null", "none", "") else False
    check("2. producer = 'Boutique Organic Farm'", 2, ok, f"FBOName='{fbo}'")


def check_3_vintage() -> None:
    v = _product.get("vintage", "")
    try:
        year = int(v)
        ok = year == 2024
    except (ValueError, TypeError):
        ok = False
        year = v
    check("3. vintage = 2024", 2, ok, f"vintage={year}")


def check_4_appellation() -> None:
    app = (_product.get("appellation", "") or "").lower()
    ok = any(t in app for t in ["burgundy", "bourgogne"]) if app else False
    check("4. appellation contains Burgundy/Bourgogne", 2, ok,
          f"appellation='{_product.get('appellation', '')}'")


def check_5_alcohol() -> None:
    try:
        alc = float(_product.get("alcohol", "0"))
        ok = abs(alc - 13.5) < 0.1
    except (ValueError, TypeError):
        alc = _product.get("alcohol", "")
        ok = False
    check("5. alcohol = 13.5%", 2, ok, f"alcohol={alc}")


def check_6_volume() -> None:
    try:
        vol = float(_product.get("volume", "0"))
        ok = abs(vol - 750.0) < 1.0 or abs(vol - 0.75) < 0.01
    except (ValueError, TypeError):
        vol = _product.get("volume", "")
        ok = False
    check("6. volume = 750 mL", 1, ok, f"volume={vol}")


def check_7_wine_type_red() -> None:
    wt = (_product.get("wine_type", "") or "").strip()
    try:
        ok = int(wt) == 2
    except (ValueError, TypeError):
        ok = False
    check("7. wine type = Red", 1, ok, f"WineType={wt} (expected 2=Red)")


def check_8_grape_pinot_noir() -> None:
    name = (_product.get("name", "") or "").lower()
    brand = (_product.get("brand", "") or "").lower()
    combined = f"{name} {brand}"
    in_text = "pinot noir" in combined or "pinot" in combined

    in_ingredients = False
    product_id = _product.get("id", "")
    if product_id:
        query = (
            "SELECT i.Name FROM ProductIngredient pi "
            "JOIN Ingredient i ON pi.IngredientId = i.Id "
            f"WHERE pi.ProductId = '{product_id}'"
        )
        rc, stdout, _ = sqlcmd(query)
        if rc == 0:
            for row in _parse_sqlcmd_rows(stdout):
                if row and "pinot" in row[0].lower():
                    in_ingredients = True
                    break
    ok = in_text or in_ingredients
    check("8. grape variety Pinot Noir referenced", 1, ok,
          f"name='{_product.get('name', '')}', brand='{_product.get('brand', '')}'")


def check_9_sulphites_allergen() -> None:
    product_id = _product.get("id", "")
    if not product_id:
        check("9. sulphites allergen declared", 2, False, "no product found")
        return
    query = (
        "SELECT i.Name, i.Allergen "
        "FROM ProductIngredient pi "
        "JOIN Ingredient i ON pi.IngredientId = i.Id "
        f"WHERE pi.ProductId = '{product_id}' AND i.Allergen = 1"
    )
    rc, stdout, _ = sqlcmd(query)
    rows = _parse_sqlcmd_rows(stdout) if rc == 0 else []
    sulphite_found = any(
        any(t in r[0].lower() for t in ["sulph", "sulfite", "bisulph", "metabisulph", "so2", "sulfit"])
        for r in rows if r
    )
    ok = sulphite_found
    detail = "sulphite allergen found" if ok else (
        f"{len(rows)} non-sulphite allergen(s)" if rows else "no allergen ingredients linked"
    )
    check("9. sulphites allergen declared", 2, ok, detail)


def check_10_ingredients_linked() -> None:
    product_id = _product.get("id", "")
    if not product_id:
        check("10. ≥1 ingredient linked", 1, False, "no product found")
        return
    query = (
        f"SELECT COUNT(*) FROM ProductIngredient WHERE ProductId = '{product_id}'"
    )
    rc, stdout, _ = sqlcmd(query)
    try:
        count = int(stdout.strip()) if rc == 0 else 0
    except ValueError:
        rows = _parse_sqlcmd_rows(stdout)
        count = int(rows[0][0]) if rows and rows[0] else 0
    ok = count >= 1
    check("10. ≥1 ingredient linked", 1, ok, f"count={count}")


def check_11_product_image() -> None:
    product_id = _product.get("id", "")
    if not product_id:
        check("11. product has image (QR/label)", 1, False, "no product found")
        return
    query = (
        f"SELECT COUNT(*) FROM Image WHERE ProductId = '{product_id}'"
    )
    rc, stdout, _ = sqlcmd(query)
    try:
        count = int(stdout.strip()) if rc == 0 else 0
    except ValueError:
        rows = _parse_sqlcmd_rows(stdout)
        count = int(rows[0][0]) if rows and rows[0] else 0
    ok = count >= 1
    check("11. product has image (QR/label)", 1, ok, f"image_count={count}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_1_product_exists()
    check_2_producer()
    check_3_vintage()
    check_4_appellation()
    check_5_alcohol()
    check_6_volume()
    check_7_wine_type_red()
    check_8_grape_pinot_noir()
    check_9_sulphites_allergen()
    check_10_ingredients_linked()
    check_11_product_image()

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
