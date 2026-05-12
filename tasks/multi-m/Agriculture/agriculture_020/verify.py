"""
Verifier for agriculture_020: Ratatouille ingredient cross-check — Recipya recipe → Grocy stock → shopping list

Checks: 8 weighted checks (14 pts total) across recipya, grocy.
Strategy: docker exec sqlite3 for Recipya; docker exec php PDO for Grocy;
          llm_judge for cross-app semantic consistency.

Required env vars:
  SERVER_HOSTNAME, GROCY_PORT, GROCY_CONTAINER, RECIPYA_PORT, RECIPYA_CONTAINER
"""

import json
import os
import subprocess
import sys

# ── Config (from env) ─────────────────────────────────────────────────────────
HOST = os.getenv("SERVER_HOSTNAME", "localhost")

GROCY_PORT = os.getenv("GROCY_PORT")
GROCY_CONTAINER = os.getenv("GROCY_CONTAINER")
RECIPYA_PORT = os.getenv("RECIPYA_PORT")
RECIPYA_CONTAINER = os.getenv("RECIPYA_CONTAINER")

for var_name, var_val in [
    ("GROCY_PORT", GROCY_PORT),
    ("GROCY_CONTAINER", GROCY_CONTAINER),
    ("RECIPYA_PORT", RECIPYA_PORT),
    ("RECIPYA_CONTAINER", RECIPYA_CONTAINER),
]:
    if not var_val:
        print(f"FATAL: {var_name} not set", file=sys.stderr)
        sys.exit(1)

GROCY_DB = "/config/data/grocy.db"
RECIPYA_DB = "/root/.config/Recipya/Database/recipya.db"

RATATOUILLE_VEGETABLES = [
    "aubergine", "eggplant", "courgette", "zucchini",
    "bell pepper", "pepper", "capsicum",
    "tomato", "onion", "garlic",
]

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


_RECIPYA_DB_CACHE: str | None = None


def _get_recipya_db() -> str:
    global _RECIPYA_DB_CACHE
    if _RECIPYA_DB_CACHE and os.path.exists(_RECIPYA_DB_CACHE):
        return _RECIPYA_DB_CACHE
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_path = tmp.name
    tmp.close()
    r = subprocess.run(
        ["docker", "cp", f"{RECIPYA_CONTAINER}:{RECIPYA_DB}", tmp_path],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        raise RuntimeError(f"docker cp failed (recipya db): {r.stderr.strip()}")
    _RECIPYA_DB_CACHE = tmp_path
    return tmp_path


def recipya_query(sql: str) -> list[dict]:
    import sqlite3 as _sqlite3
    db_path = _get_recipya_db()
    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row
    cur = conn.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def grocy_query(sql: str) -> list[dict]:
    php_code = (
        '$pdo = new PDO("sqlite:' + GROCY_DB + '");'
        "$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);"
        "$stmt = $pdo->query(" + json.dumps(sql) + ");"
        "$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);"
        "echo json_encode($rows);"
    )
    rc, out, err = docker_exec(GROCY_CONTAINER, "php", "-r", php_code)
    if rc != 0:
        raise RuntimeError(f"Grocy PHP query error: {err.strip()}")
    if not out.strip():
        return []
    return json.loads(out.strip())


def llm_judge(content: str, condition: str, timeout: int = 30) -> tuple[bool, str]:
    import urllib.request

    api_base = os.getenv("MINDRA_BASE_URL", "https://api.mindracode.com/v1")
    api_key = os.getenv("MINDRA_API_KEY", "")
    prompt = (
        f"Does the following content satisfy this condition?\n"
        f"Condition: {condition}\n\n"
        f"Content:\n{content}\n\n"
        f"Answer only YES or NO."
    )
    try:
        payload = json.dumps({
            "model": "gemini-3.0-flash-preview",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 10,
        }).encode()
        req = urllib.request.Request(
            f"{api_base}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            answer = json.loads(resp.read())["choices"][0]["message"]["content"].strip().upper()
        return answer.startswith("YES"), answer
    except Exception as e:
        return False, f"llm_judge error: {e}"


def _is_veggie_keyword(name: str) -> bool:
    name_lower = name.lower()
    return any(v in name_lower for v in RATATOUILLE_VEGETABLES)


# ── Shared state ──────────────────────────────────────────────────────────────
_recipya_recipe_id: int = -1
_recipya_recipe_name: str = ""
_recipya_ingredients: list[str] = []
_bistrot_shopping_items: list[dict] = []


# ── Individual checks ─────────────────────────────────────────────────────────

def check_1_recipya_ratatouille_exists() -> None:
    """A recipe matching 'ratatouille' exists in Recipya."""
    global _recipya_recipe_id, _recipya_recipe_name
    try:
        rows = recipya_query(
            "SELECT r.id, r.name FROM recipes r "
            "JOIN user_recipe ur ON ur.recipe_id = r.id "
            "WHERE LOWER(r.name) LIKE '%ratatouille%' "
            "ORDER BY r.id DESC LIMIT 1;"
        )
        if rows:
            _recipya_recipe_id = int(rows[0]["id"])
            _recipya_recipe_name = rows[0]["name"]
            check("1. recipya_ratatouille_exists", 2, True,
                  f"id={_recipya_recipe_id} name='{_recipya_recipe_name}'")
            return

        rows = recipya_query(
            "SELECT r.id, r.name FROM recipes r "
            "JOIN user_recipe ur ON ur.recipe_id = r.id "
            "ORDER BY r.id DESC;"
        )
        for row in rows:
            name_lower = row["name"].lower()
            if any(kw in name_lower for kw in ["ratatouille", "provenc", "vegetable stew"]):
                _recipya_recipe_id = int(row["id"])
                _recipya_recipe_name = row["name"]
                check("1. recipya_ratatouille_exists", 2, True,
                      f"id={_recipya_recipe_id} name='{_recipya_recipe_name}'")
                return

        names = [r["name"] for r in rows[:5]]
        check("1. recipya_ratatouille_exists", 2, False,
              f"no ratatouille recipe found; recent: {names}")
    except Exception as e:
        check("1. recipya_ratatouille_exists", 2, False, f"exception: {e}")


def check_2_recipya_vegetable_ingredients() -> None:
    """The Recipya ratatouille recipe has >=3 vegetable ingredients."""
    global _recipya_ingredients
    try:
        if _recipya_recipe_id < 0:
            check("2. recipya_vegetable_ingredients", 1, False, "no recipe from check 1")
            return
        rows = recipya_query(
            f"SELECT i.name FROM ingredient_recipe ir "
            f"JOIN ingredients i ON i.id = ir.ingredient_id "
            f"WHERE ir.recipe_id = {_recipya_recipe_id} "
            f"ORDER BY ir.ingredient_order;"
        )
        _recipya_ingredients = [r["name"] for r in rows]
        veggie_matches = [i for i in _recipya_ingredients if _is_veggie_keyword(i)]
        count = len(veggie_matches)
        check("2. recipya_vegetable_ingredients", 1, count >= 3,
              f"{count} veggie ingredients: {', '.join(veggie_matches[:6])}; "
              f"all ({len(_recipya_ingredients)}): {', '.join(_recipya_ingredients[:8])}")
    except Exception as e:
        check("2. recipya_vegetable_ingredients", 1, False, f"exception: {e}")


def check_3_grocy_shopping_list_has_bistrot_items() -> None:
    """Grocy shopping list has >=1 item with note containing 'Bistrot Provençal menu expansion'."""
    global _bistrot_shopping_items
    try:
        rows = grocy_query(
            "SELECT sl.id, sl.product_id, sl.amount, sl.note, "
            "COALESCE(p.name, '') AS product_name "
            "FROM shopping_list sl "
            "LEFT JOIN products p ON sl.product_id = p.id"
        )
        for item in rows:
            note = (item.get("note") or "")
            if "bistrot" in note.lower() and ("menu expansion" in note.lower()):
                _bistrot_shopping_items.append(item)

        if _bistrot_shopping_items:
            previews = [
                f"{m.get('product_name') or '(no product)'}: qty={m.get('amount')}"
                for m in _bistrot_shopping_items[:4]
            ]
            check("3. grocy_shopping_list_bistrot_items", 2, True,
                  f"{len(_bistrot_shopping_items)} item(s): {'; '.join(previews)}")
        else:
            check("3. grocy_shopping_list_bistrot_items", 2, False,
                  f"no shopping list item with 'Bistrot Provençal menu expansion' "
                  f"({len(rows)} total items)")
    except Exception as e:
        check("3. grocy_shopping_list_bistrot_items", 2, False, f"exception: {e}")


def check_4_bistrot_note_exact_text() -> None:
    """Every bistrot shopping list item has the exact note 'Bistrot Provençal menu expansion'."""
    try:
        if not _bistrot_shopping_items:
            check("4. bistrot_note_exact_text", 1, False, "no bistrot items from check 3")
            return
        exact_target = "bistrot provençal menu expansion"
        bad = []
        for item in _bistrot_shopping_items:
            note = (item.get("note") or "").strip()
            if exact_target not in note.lower():
                alt = note.lower().replace("provencal", "provençal")
                if exact_target not in alt:
                    bad.append(f"id={item['id']} note='{note[:60]}'")
        if bad:
            check("4. bistrot_note_exact_text", 1, False,
                  f"{len(bad)} item(s) with inexact note: {'; '.join(bad[:3])}")
        else:
            check("4. bistrot_note_exact_text", 1, True,
                  f"all {len(_bistrot_shopping_items)} items have correct note")
    except Exception as e:
        check("4. bistrot_note_exact_text", 1, False, f"exception: {e}")


def check_5_shopping_items_are_vegetables() -> None:
    """The bistrot shopping list items are vegetable ingredients consistent with ratatouille."""
    try:
        if not _bistrot_shopping_items:
            check("5. shopping_items_are_vegetables", 2, False, "no bistrot items from check 3")
            return
        item_names = []
        for item in _bistrot_shopping_items:
            name = item.get("product_name") or ""
            note = item.get("note") or ""
            item_names.append(name if name else note[:40])

        veggie_count = sum(1 for n in item_names if _is_veggie_keyword(n))
        total = len(item_names)
        passed = veggie_count >= 1 and veggie_count >= total * 0.5
        check("5. shopping_items_are_vegetables", 2, passed,
              f"{veggie_count}/{total} items are ratatouille vegetables: "
              f"{', '.join(item_names[:6])}")
    except Exception as e:
        check("5. shopping_items_are_vegetables", 2, False, f"exception: {e}")


def check_6_adequately_stocked_not_on_list() -> None:
    """Ingredients with stock >= 500g or >= 5 units should NOT be on the bistrot shopping list."""
    try:
        if not _bistrot_shopping_items:
            check("6. adequately_stocked_not_on_list", 2, False,
                  "no bistrot items from check 3")
            return

        stocked = grocy_query(
            "SELECT sc.product_id, sc.amount, p.name "
            "FROM stock_current sc "
            "JOIN products p ON sc.product_id = p.id "
            "WHERE sc.amount >= 5"
        )
        well_stocked_ids = {str(s["product_id"]) for s in stocked}
        well_stocked_names = {(s.get("name") or "").lower() for s in stocked}

        violations = []
        for item in _bistrot_shopping_items:
            pid = str(item.get("product_id") or "")
            pname = (item.get("product_name") or "").lower()
            if pid in well_stocked_ids or pname in well_stocked_names:
                matching_stock = [s for s in stocked
                                  if str(s["product_id"]) == pid
                                  or (s.get("name") or "").lower() == pname]
                stock_amt = matching_stock[0]["amount"] if matching_stock else "?"
                violations.append(
                    f"{item.get('product_name', '?')} (stock={stock_amt})")

        if violations:
            check("6. adequately_stocked_not_on_list", 2, False,
                  f"{len(violations)} over-stocked item(s) on list: "
                  f"{'; '.join(violations[:3])}")
        else:
            check("6. adequately_stocked_not_on_list", 2, True,
                  f"no well-stocked items wrongly added to shopping list")
    except Exception as e:
        check("6. adequately_stocked_not_on_list", 2, False, f"exception: {e}")


def check_7_shopping_amounts_reasonable() -> None:
    """Shopping list quantities are positive and reasonable (non-zero amount)."""
    try:
        if not _bistrot_shopping_items:
            check("7. shopping_amounts_reasonable", 1, False,
                  "no bistrot items from check 3")
            return
        bad = []
        for item in _bistrot_shopping_items:
            amt = float(item.get("amount") or 0)
            if amt <= 0:
                bad.append(f"{item.get('product_name', '?')}: amt={amt}")

        if bad:
            check("7. shopping_amounts_reasonable", 1, False,
                  f"{len(bad)} item(s) with zero/negative amount: {'; '.join(bad)}")
        else:
            previews = [
                f"{it.get('product_name','?')}={it.get('amount')}"
                for it in _bistrot_shopping_items[:4]
            ]
            check("7. shopping_amounts_reasonable", 1, True,
                  f"all amounts positive: {'; '.join(previews)}")
    except Exception as e:
        check("7. shopping_amounts_reasonable", 1, False, f"exception: {e}")


def check_8_cross_app_ingredients_match() -> None:
    """LLM judge: Grocy shopping list items correspond to ingredients in the Recipya ratatouille recipe."""
    try:
        if not _bistrot_shopping_items:
            check("8. cross_app_ingredients_match", 3, False,
                  "no bistrot items from check 3")
            return
        if not _recipya_ingredients:
            check("8. cross_app_ingredients_match", 3, False,
                  "no recipya ingredients from check 2")
            return

        shopping_names = [
            item.get("product_name") or item.get("note", "unknown")
            for item in _bistrot_shopping_items
        ]
        content = (
            f"Recipya ratatouille recipe ingredients: {', '.join(_recipya_ingredients)}\n\n"
            f"Grocy shopping list items added for the restaurant: {', '.join(shopping_names)}"
        )
        condition = (
            "The items added to the Grocy shopping list correspond semantically to "
            "ingredients required by the Ratatouille recipe from Recipya. "
            "The shopping list items should be a SUBSET of the recipe's ingredients — "
            "specifically, only the under-stocked or missing ones. "
            "Items that are clearly unrelated to ratatouille should cause a NO."
        )
        passed, detail = llm_judge(content, condition)
        check("8. cross_app_ingredients_match", 3, passed, detail)
    except Exception as e:
        check("8. cross_app_ingredients_match", 3, False, f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_1_recipya_ratatouille_exists()
    check_2_recipya_vegetable_ingredients()
    check_3_grocy_shopping_list_has_bistrot_items()
    check_4_bistrot_note_exact_text()
    check_5_shopping_items_are_vegetables()
    check_6_adequately_stocked_not_on_list()
    check_7_shopping_amounts_reasonable()
    check_8_cross_app_ingredients_match()

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
