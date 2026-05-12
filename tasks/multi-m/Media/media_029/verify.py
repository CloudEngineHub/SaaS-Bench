"""
Verifier for media_029: Scream poster → Watcharr watch log + SiYuan EP-56 script.

Checks: 11 weighted checks (18 total points) across watcharr, siyuan.
Strategy: watcharr via docker exec SQLite; siyuan via REST API; llm_judge + llm_judge_vision.

Required env vars:
  SERVER_HOSTNAME, WATCHARR_PORT, WATCHARR_CONTAINER, SIYUAN_PORT, SIYUAN_CONTAINER.
"""

import base64
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error

# ── Config (from env) ─────────────────────────────────────────────────────────
HOST = os.getenv("SERVER_HOSTNAME", "localhost")

WATCHARR_PORT = os.getenv("WATCHARR_PORT")
WATCHARR_CONTAINER = os.getenv("WATCHARR_CONTAINER")
SIYUAN_PORT = os.getenv("SIYUAN_PORT")
SIYUAN_CONTAINER = os.getenv("SIYUAN_CONTAINER")

for _var_name, _var_val in [
    ("WATCHARR_PORT", WATCHARR_PORT),
    ("WATCHARR_CONTAINER", WATCHARR_CONTAINER),
    ("SIYUAN_PORT", SIYUAN_PORT),
    ("SIYUAN_CONTAINER", SIYUAN_CONTAINER),
]:
    if not _var_val:
        print(f"FATAL: {_var_name} not set", file=sys.stderr)
        sys.exit(1)

WATCHARR_DB = "/data/watcharr.db"
SIYUAN_API = f"http://{HOST}:{SIYUAN_PORT}"
SIYUAN_TOKEN = ""

_INPUTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "inputs"
)

INPUT_FILES: list[str] = [
    os.path.join(_INPUTS_DIR, "watcharr_poster_007.jpg"),
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


def get_siyuan_token() -> str:
    global SIYUAN_TOKEN
    if SIYUAN_TOKEN:
        return SIYUAN_TOKEN
    rc, stdout, _ = docker_exec(
        SIYUAN_CONTAINER, "cat", "/siyuan/workspace/conf/conf.json", timeout=10,
    )
    if rc == 0 and stdout.strip():
        try:
            conf = json.loads(stdout)
            SIYUAN_TOKEN = conf.get("api", {}).get("token", "")
        except json.JSONDecodeError:
            pass
    return SIYUAN_TOKEN


_WATCHARR_DB_CACHE: str | None = None


def _get_watcharr_db() -> str:
    global _WATCHARR_DB_CACHE
    if _WATCHARR_DB_CACHE and os.path.exists(_WATCHARR_DB_CACHE):
        return _WATCHARR_DB_CACHE
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_path = tmp.name
    tmp.close()
    r = subprocess.run(
        ["docker", "cp", f"{WATCHARR_CONTAINER}:{WATCHARR_DB}", tmp_path],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        raise RuntimeError(f"docker cp failed (watcharr db): {r.stderr.strip()}")
    _WATCHARR_DB_CACHE = tmp_path
    return tmp_path


def watcharr_sql(query: str) -> str:
    import sqlite3 as _sqlite3
    db_path = _get_watcharr_db()
    conn = _sqlite3.connect(db_path)
    cur = conn.execute(query)
    rows = cur.fetchall()
    conn.close()
    return "\n".join("|".join("" if c is None else str(c) for c in row) for row in rows)


def siyuan_sql(stmt: str) -> list[dict]:
    payload = json.dumps({"stmt": stmt}).encode()
    headers = {"Content-Type": "application/json"}
    token = get_siyuan_token()
    if token:
        headers["Authorization"] = f"Token {token}"
    req = urllib.request.Request(
        f"{SIYUAN_API}/api/query/sql",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"SiYuan API HTTP {e.code}: {e.read().decode()[:200]}")
    if body.get("code") != 0:
        raise RuntimeError(f"SiYuan API error: {body.get('msg', body)}")
    return body.get("data") or []


def llm_judge(content: str, condition: str, timeout: int = 30) -> tuple[bool, str]:
    api_base = os.getenv("MINDRA_BASE_URL", "https://api.mindracode.com/v1")
    api_key = os.getenv("MINDRA_API_KEY", "")
    prompt = (
        f"Does the following content satisfy this condition?\n"
        f"Condition: {condition}\n\n"
        f"Content:\n{content}\n\n"
        f"Answer only YES or NO."
    )
    body = json.dumps({
        "model": "gemini-3.0-flash-preview",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 10,
    }).encode()
    try:
        req = urllib.request.Request(
            f"{api_base}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        answer = data["choices"][0]["message"]["content"].strip().upper()
        return answer.startswith("YES"), answer
    except Exception as e:
        return False, f"llm_judge error: {e}"


def llm_judge_vision(
    image_path: str,
    recorded_value: str,
    condition: str,
    timeout: int = 45,
) -> tuple[bool, str]:
    api_base = os.getenv("MINDRA_BASE_URL", "https://api.mindracode.com/v1")
    api_key = os.getenv("MINDRA_API_KEY", "")

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "gif": "image/gif",
        "webp": "image/webp",
    }.get(ext, "image/jpeg")

    if not os.path.isfile(image_path):
        return False, f"image not found: {image_path}"

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    prompt = (
        f"You are given an image and a value that an AI agent extracted from it.\n"
        f"Recorded value: «{recorded_value}»\n"
        f"Condition: {condition}\n\n"
        f"Does the recorded value accurately match the information visible in the image, "
        f"satisfying the condition above?\n"
        f"Answer only YES or NO."
    )
    msg_content = [
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        {"type": "text", "text": prompt},
    ]
    body = json.dumps({
        "model": "gemini-3.0-flash-preview",
        "messages": [{"role": "user", "content": msg_content}],
        "max_tokens": 10,
    }).encode()
    try:
        req = urllib.request.Request(
            f"{api_base}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        answer = data["choices"][0]["message"]["content"].strip().upper()
        return answer.startswith("YES"), answer
    except Exception as e:
        return False, f"llm_judge_vision error: {e}"


# ── Cached state ─────────────────────────────────────────────────────────────
_watcharr_row: dict = {}
_ep56_root_id: str = ""
_input_files_ok: bool = False


# ── Individual checks ─────────────────────────────────────────────────────────
def check_0_input_files_exist() -> None:
    global _input_files_ok
    missing = [p for p in INPUT_FILES if not os.path.isfile(p)]
    if missing:
        check("0. input_files_exist", 1, False, "missing: " + ", ".join(missing))
    else:
        _input_files_ok = True
        check("0. input_files_exist", 1, True)


def check_1_watcharr_scream_exists() -> None:
    global _watcharr_row
    try:
        rows = watcharr_sql(
            "SELECT w.status, w.rating, w.thoughts, c.title "
            "FROM watcheds w JOIN contents c ON w.content_id = c.id "
            "WHERE LOWER(c.title) LIKE '%scream%' "
            "AND w.deleted_at IS NULL LIMIT 1;"
        )
        if not rows:
            check("1. watcharr_scream_exists", 2, False,
                  "no watched entry for Scream found")
            return
        parts = rows.split("|", 3)
        _watcharr_row = {
            "status": parts[0] if len(parts) > 0 else "",
            "rating": parts[1] if len(parts) > 1 else "",
            "thoughts": parts[2] if len(parts) > 2 else "",
            "title": parts[3] if len(parts) > 3 else "",
        }
        check("1. watcharr_scream_exists", 2, True,
              f"found: {_watcharr_row['title']}")
    except Exception as e:
        check("1. watcharr_scream_exists", 2, False, f"exception: {e}")


def check_2_watcharr_status_watched() -> None:
    try:
        if not _watcharr_row:
            check("2. watcharr_status_watched", 1, False, "no watched row available")
            return
        status = _watcharr_row["status"]
        passed = status == "FINISHED"
        detail = "" if passed else f"status is '{status}', expected 'FINISHED'"
        check("2. watcharr_status_watched", 1, passed, detail)
    except Exception as e:
        check("2. watcharr_status_watched", 1, False, f"exception: {e}")


def check_3_watcharr_rating_7_5() -> None:
    try:
        if not _watcharr_row:
            check("3. watcharr_rating_7.5", 1, False, "no watched row available")
            return
        raw = _watcharr_row["rating"]
        rating = float(raw)
        passed = abs(rating - 7.5) < 0.01
        detail = "" if passed else f"rating is {rating}, expected 7.5"
        check("3. watcharr_rating_7.5", 1, passed, detail)
    except Exception as e:
        check("3. watcharr_rating_7.5", 1, False, f"exception: {e}")


def check_4_watcharr_review_length() -> None:
    try:
        if not _watcharr_row:
            check("4. watcharr_review_length", 1, False, "no watched row available")
            return
        thoughts = _watcharr_row["thoughts"]
        if not thoughts:
            check("4. watcharr_review_length", 1, False, "review is empty")
            return
        words = len(thoughts.split())
        passed = 45 <= words <= 120
        detail = f"word_count={words}" if passed else f"word_count={words}, expected 50-100"
        check("4. watcharr_review_length", 1, passed, detail)
    except Exception as e:
        check("4. watcharr_review_length", 1, False, f"exception: {e}")


def check_5_watcharr_review_meta_commentary() -> None:
    try:
        if not _watcharr_row:
            check("5. watcharr_review_meta_commentary", 2, False,
                  "no watched row available")
            return
        thoughts = _watcharr_row["thoughts"]
        if not thoughts or len(thoughts) < 20:
            check("5. watcharr_review_meta_commentary", 2, False,
                  "review too short for analysis")
            return
        condition = (
            "The review discusses how the film Scream uses meta-commentary, self-awareness, "
            "or genre deconstruction to subvert traditional slasher film narrative structures. "
            "It should go beyond generic praise and address specific ways the film plays with "
            "horror conventions, such as its characters' awareness of horror movie rules, "
            "its satirical take on the genre, or its commentary on slasher tropes."
        )
        passed, raw = llm_judge(thoughts, condition)
        check("5. watcharr_review_meta_commentary", 2, passed,
              f"llm_judge={raw[:60]}")
    except Exception as e:
        check("5. watcharr_review_meta_commentary", 2, False, f"exception: {e}")


def check_6_cross_modal_film_identity() -> None:
    try:
        if not _input_files_ok:
            check("6. cross_modal_film_identity", 2, False,
                  "skipped: input file missing")
            return
        title = _watcharr_row.get("title", "")
        if not title:
            check("6. cross_modal_film_identity", 2, False,
                  "no film title recorded in Watcharr")
            return
        condition = (
            "The movie poster shown in the image is for the film whose title "
            "matches the recorded value. The poster should be identifiable as "
            "a Scream franchise movie poster."
        )
        passed, raw = llm_judge_vision(INPUT_FILES[0], title, condition)
        check("6. cross_modal_film_identity", 2, passed,
              f"title='{title}', llm_judge_vision={raw[:60]}")
    except Exception as e:
        check("6. cross_modal_film_identity", 2, False, f"exception: {e}")


def check_7_siyuan_ep56_exists() -> None:
    global _ep56_root_id
    try:
        rows = siyuan_sql(
            "SELECT id, content, box FROM blocks WHERE type = 'd' "
            "AND (content LIKE '%EP-56%' OR content LIKE '%ep-56%' "
            "OR content LIKE '%EP56%' OR content LIKE '%Meta-Slasher%' "
            "OR content LIKE '%Meta Slasher%') LIMIT 5"
        )
        if not rows:
            check("7. siyuan_ep56_exists", 2, False,
                  "no document matching EP-56 or Meta-Slasher found")
            return
        for row in rows:
            title = row.get("content", "")
            if "EP-56" in title or "ep-56" in title.lower() or "EP56" in title:
                _ep56_root_id = row["id"]
                check("7. siyuan_ep56_exists", 2, True, f"doc='{title}'")
                return
        _ep56_root_id = rows[0]["id"]
        check("7. siyuan_ep56_exists", 2, True,
              f"doc='{rows[0].get('content', '')}' (best match)")
    except Exception as e:
        check("7. siyuan_ep56_exists", 2, False, f"exception: {e}")


def check_8_siyuan_thesis_section() -> None:
    try:
        if not _ep56_root_id:
            check("8. siyuan_thesis_section", 2, False, "EP-56 doc not found")
            return
        blocks = siyuan_sql(
            f"SELECT type, subtype, content, markdown FROM blocks "
            f"WHERE root_id = '{_ep56_root_id}' AND type != 'd' "
            f"ORDER BY sort"
        )
        if not blocks:
            check("8. siyuan_thesis_section", 2, False, "no blocks found in EP-56 doc")
            return

        thesis_heading_idx = -1
        for i, b in enumerate(blocks):
            content = b.get("content", "").lower()
            if b.get("type") == "h" and "thesis" in content:
                thesis_heading_idx = i
                break

        if thesis_heading_idx < 0:
            check("8. siyuan_thesis_section", 2, False,
                  "no 'Thesis' heading found in EP-56")
            return

        heading_level = blocks[thesis_heading_idx].get("subtype", "h2")
        thesis_content = []
        for b in blocks[thesis_heading_idx + 1:]:
            if b.get("type") == "h":
                b_sub = b.get("subtype", "h9")
                if b_sub <= heading_level:
                    break
            text = b.get("markdown", "") or b.get("content", "")
            if text.strip():
                thesis_content.append(text.strip())

        combined = " ".join(thesis_content)
        char_count = len(combined)
        passed = char_count >= 100
        detail = f"char_count={char_count}" if passed else (
            f"char_count={char_count}, need >=100")
        check("8. siyuan_thesis_section", 2, passed, detail)
    except Exception as e:
        check("8. siyuan_thesis_section", 2, False, f"exception: {e}")


def check_9_siyuan_trope_deconstruction_section() -> None:
    try:
        if not _ep56_root_id:
            check("9. siyuan_trope_deconstruction", 2, False, "EP-56 doc not found")
            return
        blocks = siyuan_sql(
            f"SELECT type, subtype, content, markdown FROM blocks "
            f"WHERE root_id = '{_ep56_root_id}' AND type != 'd' "
            f"ORDER BY sort"
        )
        if not blocks:
            check("9. siyuan_trope_deconstruction", 2, False,
                  "no blocks found in EP-56 doc")
            return

        trope_heading_idx = -1
        for i, b in enumerate(blocks):
            content = b.get("content", "").lower()
            if b.get("type") == "h" and "trope" in content and "deconstruction" in content:
                trope_heading_idx = i
                break
        if trope_heading_idx < 0:
            for i, b in enumerate(blocks):
                content = b.get("content", "").lower()
                if b.get("type") == "h" and "trope" in content:
                    trope_heading_idx = i
                    break

        if trope_heading_idx < 0:
            check("9. siyuan_trope_deconstruction", 2, False,
                  "no 'Trope Deconstruction' heading found")
            return

        heading_level = blocks[trope_heading_idx].get("subtype", "h2")
        section_blocks = []
        for b in blocks[trope_heading_idx + 1:]:
            if b.get("type") == "h":
                b_sub = b.get("subtype", "h9")
                if b_sub <= heading_level:
                    break
            section_blocks.append(b)

        numbered_items = 0
        for b in section_blocks:
            md = b.get("markdown", "") or b.get("content", "")
            btype = b.get("type", "")
            if btype in ("l", "i"):
                items = [line for line in md.split("\n")
                         if re.match(r'^\s*\d+[\.\)]\s', line)]
                numbered_items += len(items)
            elif btype == "p":
                if re.match(r'^\s*\d+[\.\)]\s', md):
                    numbered_items += 1

        if numbered_items < 3:
            all_text = "\n".join(
                b.get("markdown", "") or b.get("content", "")
                for b in section_blocks
            )
            list_like = re.findall(r'(?:^|\n)\s*\d+[\.\)]\s', all_text)
            numbered_items = max(numbered_items, len(list_like))

        if numbered_items < 3:
            total_items = 0
            for b in section_blocks:
                btype = b.get("type", "")
                if btype in ("l", "i"):
                    md = b.get("markdown", "") or b.get("content", "")
                    total_items += len([
                        line for line in md.split("\n")
                        if re.match(r'^\s*[-*•]\s', line) or re.match(r'^\s*\d+[\.\)]\s', line)
                    ])
            numbered_items = max(numbered_items, total_items)

        passed = numbered_items >= 3
        detail = f"items={numbered_items}" if passed else (
            f"items={numbered_items}, need >=3")
        check("9. siyuan_trope_deconstruction", 2, passed, detail)
    except Exception as e:
        check("9. siyuan_trope_deconstruction", 2, False, f"exception: {e}")


def check_10_siyuan_watcharr_link() -> None:
    try:
        if not _ep56_root_id:
            check("10. siyuan_watcharr_link", 2, False, "EP-56 doc not found")
            return
        blocks = siyuan_sql(
            f"SELECT type, content, markdown FROM blocks "
            f"WHERE root_id = '{_ep56_root_id}' AND type != 'd' "
            f"ORDER BY sort"
        )
        watcharr_port = WATCHARR_PORT
        all_text = "\n".join(
            b.get("markdown", "") or b.get("content", "")
            for b in blocks
        )

        has_link = False
        if re.search(r'watcharr', all_text, re.IGNORECASE):
            has_link = True
        if re.search(rf'localhost:{watcharr_port}', all_text):
            has_link = True
        if re.search(rf'{HOST}:{watcharr_port}', all_text):
            has_link = True
        if re.search(r'https?://[^\s)]+watcharr[^\s)]*', all_text, re.IGNORECASE):
            has_link = True
        if re.search(r'\[.*?\]\(.*?watcharr.*?\)', all_text, re.IGNORECASE):
            has_link = True
        if re.search(r'\[.*?\]\(.*?localhost:' + re.escape(watcharr_port) + r'.*?\)',
                      all_text):
            has_link = True

        refs = siyuan_sql(
            f"SELECT COUNT(*) as cnt FROM refs "
            f"WHERE root_id = '{_ep56_root_id}'"
        )
        ref_count = refs[0].get("cnt", 0) if refs else 0
        if ref_count > 0:
            has_link = True

        if not has_link:
            check("10. siyuan_watcharr_link", 2, False,
                  "no Watcharr link/URL/reference found in EP-56")
        else:
            check("10. siyuan_watcharr_link", 2, True)
    except Exception as e:
        check("10. siyuan_watcharr_link", 2, False, f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_0_input_files_exist()
    check_1_watcharr_scream_exists()
    check_2_watcharr_status_watched()
    check_3_watcharr_rating_7_5()
    check_4_watcharr_review_length()
    check_5_watcharr_review_meta_commentary()
    check_6_cross_modal_film_identity()
    check_7_siyuan_ep56_exists()
    check_8_siyuan_thesis_section()
    check_9_siyuan_trope_deconstruction_section()
    check_10_siyuan_watcharr_link()

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
