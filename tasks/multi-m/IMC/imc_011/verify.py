"""
Verifier for imc_011: Deep-dive episode comparing Valley of Fear (novel) vs Game of Shadows (film)

Checks: 11 weighted checks across watcharr, booklore, siyuan.
Strategy: docker exec SQLite (watcharr), docker exec MariaDB (booklore), REST API (siyuan), llm_judge (content quality).

Required env vars:
  SERVER_HOSTNAME, WATCHARR_PORT, WATCHARR_CONTAINER,
  BOOKLORE_PORT, BOOKLORE_CONTAINER,
  SIYUAN_PORT, SIYUAN_CONTAINER
"""

import os
import sys
import subprocess
import json
import re

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import requests

# ── Config (from env) ─────────────────────────────────────────────────────────
HOST = os.getenv("SERVER_HOSTNAME", "localhost")

WATCHARR_PORT = os.getenv("WATCHARR_PORT")
WATCHARR_CONTAINER = os.getenv("WATCHARR_CONTAINER")
BOOKLORE_PORT = os.getenv("BOOKLORE_PORT")
BOOKLORE_CONTAINER = os.getenv("BOOKLORE_CONTAINER")
SIYUAN_PORT = os.getenv("SIYUAN_PORT")
SIYUAN_CONTAINER = os.getenv("SIYUAN_CONTAINER")

_missing = []
for var in ["WATCHARR_PORT", "WATCHARR_CONTAINER",
            "BOOKLORE_PORT", "BOOKLORE_CONTAINER",
            "SIYUAN_PORT", "SIYUAN_CONTAINER"]:
    if not os.getenv(var):
        _missing.append(var)
if _missing:
    print(f"FATAL: {', '.join(_missing)} not set", file=sys.stderr)
    sys.exit(1)

BOOKLORE_DB_CONTAINER = os.getenv("BOOKLORE_DB_CONTAINER", BOOKLORE_CONTAINER + "-db")

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


# ── Watcharr helpers (SQLite via docker exec) ────────────────────────────────
_watcharr_db_path: str | None = None


def _find_watcharr_db() -> str:
    global _watcharr_db_path
    if _watcharr_db_path is not None:
        return _watcharr_db_path
    for candidate in ["/data/watcharr.db", "/data/database.sqlite", "/app/watcharr.db"]:
        rc, _, _ = docker_exec(WATCHARR_CONTAINER, "test", "-f", candidate, timeout=5)
        if rc == 0:
            _watcharr_db_path = candidate
            return _watcharr_db_path
    rc, stdout, _ = docker_exec(
        WATCHARR_CONTAINER, "find", "/", "-maxdepth", "4",
        "-name", "*.db", "-o", "-name", "*.sqlite",
        timeout=10,
    )
    for line in stdout.strip().splitlines():
        line = line.strip()
        if "watcharr" in line.lower() or "database" in line.lower():
            _watcharr_db_path = line
            return _watcharr_db_path
    _watcharr_db_path = "/data/watcharr.db"
    return _watcharr_db_path


def watcharr_sql(sql: str, timeout: int = 15) -> tuple[int, str, str]:
    db = _find_watcharr_db()
    rc, out, err = docker_exec(
        WATCHARR_CONTAINER, "sqlite3", "-separator", "\t", db, sql,
        timeout=timeout,
    )
    if rc != 0 and ("not found" in err.lower() or "executable file" in err.lower()):
        docker_exec(
            WATCHARR_CONTAINER, "sh", "-c",
            "apk add --no-cache sqlite 2>/dev/null || "
            "(apt-get update -qq && apt-get install -y -qq sqlite3) 2>/dev/null",
            timeout=60,
        )
        rc, out, err = docker_exec(
            WATCHARR_CONTAINER, "sqlite3", "-separator", "\t", db, sql,
            timeout=timeout,
        )
    return rc, out, err


# ── Booklore helpers (MariaDB via docker exec) ──────────────────────────────
def mariadb_query(query: str, timeout: int = 15) -> str:
    r = subprocess.run(
        [
            "docker", "exec", BOOKLORE_DB_CONTAINER,
            "mariadb", "-u", "booklore",
            "-pChangeMe_BookLoreApp_2025!",
            "--default-character-set=utf8mb4",
            "-D", "booklore",
            "-N", "-B", "-e", query,
        ],
        capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode != 0:
        r2 = subprocess.run(
            [
                "docker", "exec", BOOKLORE_DB_CONTAINER,
                "mysql", "-u", "booklore",
                "-pChangeMe_BookLoreApp_2025!",
                "--default-character-set=utf8mb4",
                "-D", "booklore",
                "-N", "-B", "-e", query,
            ],
            capture_output=True, text=True, timeout=timeout,
        )
        return r2.stdout.strip()
    return r.stdout.strip()


# ── SiYuan helpers (REST API) ───────────────────────────────────────────────
_siyuan_token: str | None = None


def _get_siyuan_token() -> str:
    global _siyuan_token
    if _siyuan_token is not None:
        return _siyuan_token
    rc, out, _ = docker_exec(
        SIYUAN_CONTAINER, "cat", "/siyuan/workspace/conf/conf.json", timeout=10,
    )
    if rc == 0 and out.strip():
        try:
            conf = json.loads(out)
            _siyuan_token = conf.get("api", {}).get("token", "")
        except (json.JSONDecodeError, AttributeError):
            _siyuan_token = ""
    else:
        _siyuan_token = ""
    return _siyuan_token


def siyuan_api(endpoint: str, payload: dict, timeout: int = 15) -> dict:
    url = f"http://{HOST}:{SIYUAN_PORT}{endpoint}"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = _get_siyuan_token()
    if token:
        headers["Authorization"] = f"Token {token}"
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != 0:
            raise RuntimeError(f"SiYuan API error: {body.get('msg', 'unknown')}")
        return body.get("data", {})
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"SiYuan request failed: {e}")


def siyuan_sql(stmt: str) -> list:
    data = siyuan_api("/api/query/sql", {"stmt": stmt})
    if isinstance(data, list):
        return data
    return []


# ── LLM judge helper ────────────────────────────────────────────────────────
def llm_judge(content: str, condition: str, timeout: int = 30) -> tuple[bool, str]:
    api_base = os.getenv("MINDRA_BASE_URL", "https://api.mindracode.com/v1")
    api_key = os.getenv("MINDRA_API_KEY", "")
    if not api_key:
        return False, "MINDRA_API_KEY not set"
    prompt = (
        f"Does the following content satisfy this condition?\n"
        f"Condition: {condition}\n\n"
        f"Content:\n{content}\n\n"
        f"Answer only YES or NO."
    )
    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            json={"model": "gemini-3.0-flash-preview",
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 10},
            timeout=timeout,
        )
        resp.raise_for_status()
        answer = resp.json()["choices"][0]["message"]["content"].strip().upper()
        return answer.startswith("YES"), answer
    except Exception as e:
        return False, f"llm_judge error: {e}"


# ── Shared state ─────────────────────────────────────────────────────────────
_film_data: dict | None = None
_book_id: str | None = None
_book_notes_text: str = ""
_siyuan_doc_id: str | None = None
_siyuan_full_content: str = ""
_siyuan_full_markdown: str = ""
_siyuan_headings: list[str] = []


# ── Individual checks ────────────────────────────────────────────────────────

def check_1_watcharr_film_exists() -> None:
    """Film 'Sherlock Holmes: A Game of Shadows' tracked in Watcharr."""
    global _film_data
    try:
        rc, out, err = watcharr_sql(
            "SELECT c.id, c.title, w.status, w.rating, w.thoughts "
            "FROM contents c "
            "JOIN watcheds w ON w.content_id = c.id "
            "WHERE c.type = 'movie' "
            "AND (c.title LIKE '%Game of Shadows%' OR c.title LIKE '%game of shadows%') "
            "AND w.deleted_at IS NULL "
            "LIMIT 1;"
        )
        if rc != 0:
            check("1. Watcharr: film found", 1, False, f"sqlite error: {err.strip()[:200]}")
            return
        lines = [l for l in out.strip().splitlines() if l.strip()]
        if not lines:
            rc2, all_titles, _ = watcharr_sql(
                "SELECT c.title FROM contents c JOIN watcheds w ON w.content_id = c.id LIMIT 10;"
            )
            check("1. Watcharr: film found", 1, False,
                  f"film not found; watched titles: {all_titles.strip()[:200]}")
            return
        parts = lines[0].split("\t")
        _film_data = {
            "content_id": parts[0] if len(parts) > 0 else "",
            "title": parts[1] if len(parts) > 1 else "",
            "status": parts[2] if len(parts) > 2 else "",
            "rating": parts[3] if len(parts) > 3 else "",
            "thoughts": parts[4] if len(parts) > 4 else "",
        }
        check("1. Watcharr: film found", 1, True,
              f"title='{_film_data['title']}'")
    except Exception as e:
        check("1. Watcharr: film found", 1, False, f"exception: {e}")


def check_2_watcharr_status_rating() -> None:
    """Film status is WATCHED/FINISHED and rating is 8/10."""
    if not _film_data:
        check("2. Watcharr: status Watched + rating 8/10", 1, False,
              "skipped: film not found")
        return
    try:
        status = _film_data["status"]
        rating_str = _film_data["rating"]
        status_ok = status.upper() == "FINISHED"
        try:
            rating_val = float(rating_str)
        except (ValueError, TypeError):
            rating_val = -1
        rating_ok = abs(rating_val - 8.0) < 0.5
        passed = status_ok and rating_ok
        detail = f"status='{status}', rating={rating_str}"
        if not status_ok:
            detail += " (expected FINISHED)"
        if not rating_ok:
            detail += " (expected 8.0)"
        check("2. Watcharr: status Watched + rating 8/10", 1, passed, detail)
    except Exception as e:
        check("2. Watcharr: status Watched + rating 8/10", 1, False, f"exception: {e}")


def check_3_watcharr_review_moriarty() -> None:
    """Review focuses on Moriarty adaptation treatment, not plot retelling."""
    if not _film_data:
        check("3. Watcharr: review on Moriarty adaptation", 2, False,
              "skipped: film not found")
        return
    try:
        thoughts = _film_data.get("thoughts", "")
        if not thoughts or len(thoughts) < 50:
            check("3. Watcharr: review on Moriarty adaptation", 2, False,
                  f"review too short: {len(thoughts)} chars (need >=50)")
            return
        passed, answer = llm_judge(
            thoughts,
            "The review focuses on the adaptation treatment of Moriarty — "
            "his characterisation, how Guy Ritchie portrays him compared to the source, "
            "or narrative/directorial choices around the villain — "
            "NOT a generic plot summary or generic praise like 'great film, exciting action'."
        )
        check("3. Watcharr: review on Moriarty adaptation", 2, passed,
              f"llm_judge={answer}, review_len={len(thoughts)}")
    except Exception as e:
        check("3. Watcharr: review on Moriarty adaptation", 2, False, f"exception: {e}")


def check_4_booklore_book_exists() -> None:
    """'The Valley of Fear' exists in Booklore."""
    global _book_id
    try:
        result = mariadb_query(
            "SELECT bm.book_id FROM book_metadata bm "
            "WHERE bm.title LIKE '%Valley of Fear%' LIMIT 1"
        )
        if result:
            _book_id = result.strip().split("\n")[0].strip()
            check("4. Booklore: Valley of Fear exists", 1, True,
                  f"book_id={_book_id}")
        else:
            all_q = "SELECT bm.book_id, bm.title FROM book_metadata bm LIMIT 10"
            all_titles = mariadb_query(all_q)
            check("4. Booklore: Valley of Fear exists", 1, False,
                  f"book not found; available: {all_titles[:200]}")
    except Exception as e:
        check("4. Booklore: Valley of Fear exists", 1, False, f"exception: {e}")


def check_5_booklore_notes_exist() -> None:
    """At least 5 reading notes on The Valley of Fear."""
    global _book_notes_text
    if not _book_id:
        check("5. Booklore: >=5 reading notes", 2, False, "skipped: book not found")
        return
    try:
        notes_v2 = mariadb_query(
            f"SELECT note_content FROM book_notes_v2 WHERE book_id = {_book_id}"
        )
        notes_v1 = mariadb_query(
            f"SELECT content FROM book_notes WHERE book_id = {_book_id}"
        )
        all_notes_raw = notes_v2 or notes_v1
        if not all_notes_raw:
            check("5. Booklore: >=5 reading notes", 2, False, "no notes found (v1 or v2)")
            return

        note_lines = [l.strip() for l in all_notes_raw.strip().split("\n") if l.strip()]
        _book_notes_text = "\n".join(note_lines)

        count_v2 = mariadb_query(
            f"SELECT COUNT(*) FROM book_notes_v2 WHERE book_id = {_book_id}"
        )
        count_v1 = mariadb_query(
            f"SELECT COUNT(*) FROM book_notes WHERE book_id = {_book_id}"
        )
        try:
            note_count = max(int(count_v2 or "0"), int(count_v1 or "0"))
        except ValueError:
            note_count = len(note_lines)

        if note_count < 5 and len(note_lines) >= 5:
            note_count = len(note_lines)

        passed = note_count >= 5
        check("5. Booklore: >=5 reading notes", 2, passed, f"count={note_count}")
    except Exception as e:
        check("5. Booklore: >=5 reading notes", 2, False, f"exception: {e}")


def check_6_booklore_notes_dimensions() -> None:
    """Notes cover at least 3 distinct dimensions of book-film differences."""
    if not _book_notes_text:
        check("6. Booklore: notes span >=3 dimensions", 2, False,
              "skipped: no notes text")
        return
    try:
        passed, answer = llm_judge(
            _book_notes_text,
            "The reading notes list at least 5 specific differences between the novel "
            "'The Valley of Fear' by Arthur Conan Doyle and the film "
            "'Sherlock Holmes: A Game of Shadows' (2011). The differences must span at least "
            "3 distinct dimensions from among: "
            "(1) characterisation (Moriarty's presence and portrayal), "
            "(2) plot/mystery structure, "
            "(3) setting and historical period, "
            "(4) visual/linguistic style, "
            "(5) supporting character functions."
        )
        check("6. Booklore: notes span >=3 dimensions", 2, passed,
              f"llm_judge={answer}")
    except Exception as e:
        check("6. Booklore: notes span >=3 dimensions", 2, False, f"exception: {e}")


def check_7_siyuan_doc_exists() -> None:
    """SiYuan has a document titled EP-44 about Two Narratives of the Valley of Fear."""
    global _siyuan_doc_id
    try:
        rows = siyuan_sql(
            "SELECT id, content FROM blocks "
            "WHERE type = 'd' AND content LIKE '%EP-44%'"
        )
        if rows:
            _siyuan_doc_id = rows[0].get("id", "")
            title = rows[0].get("content", "")
            check("7. SiYuan: EP-44 doc exists", 1, True,
                  f"doc_id={_siyuan_doc_id}, title='{title}'")
            return

        rows_alt = siyuan_sql(
            "SELECT id, content FROM blocks "
            "WHERE type = 'd' AND (content LIKE '%Valley of Fear%' OR content LIKE '%恐惧谷%')"
        )
        if rows_alt:
            _siyuan_doc_id = rows_alt[0].get("id", "")
            title = rows_alt[0].get("content", "")
            check("7. SiYuan: EP-44 doc exists", 1, True,
                  f"doc_id={_siyuan_doc_id}, title='{title}' (alt match)")
            return

        all_docs = siyuan_sql(
            "SELECT id, content FROM blocks WHERE type = 'd' LIMIT 10"
        )
        titles = [r.get("content", "") for r in (all_docs or [])]
        check("7. SiYuan: EP-44 doc exists", 1, False,
              f"no EP-44 doc found; available docs: {titles[:5]}")
    except Exception as e:
        check("7. SiYuan: EP-44 doc exists", 1, False, f"exception: {e}")


def check_8_siyuan_four_sections() -> None:
    """EP-44 has all 4 required sections: intro, difference analysis, creator intent, recommendation."""
    global _siyuan_full_content, _siyuan_full_markdown, _siyuan_headings
    if not _siyuan_doc_id:
        check("8. SiYuan: all 4 required sections", 2, False,
              "skipped: doc not found")
        return
    try:
        blocks = siyuan_sql(
            f"SELECT type, subtype, content, markdown FROM blocks "
            f"WHERE root_id = '{_siyuan_doc_id}' AND type != 'd' ORDER BY sort"
        )
        _siyuan_full_content = "\n".join(
            b.get("content", "") for b in (blocks or [])
        )
        _siyuan_full_markdown = "\n".join(
            b.get("markdown", "") for b in (blocks or [])
        )
        _siyuan_headings = [
            b.get("content", "") for b in (blocks or []) if b.get("type") == "h"
        ]

        section_patterns = {
            "Introduction": r"(导言|introduction|intro|背景|context)",
            "Difference Analysis": r"(差异|differ|comparison|对比|核心差异|分析)",
            "Creator Intent": r"(创作者意图|creator.?intent|意图|vision|cinematic.*goal|novelistic)",
            "Recommendation": r"(结论|conclusion|推荐|recommend|version)",
        }
        found_sections = []
        missing_sections = []
        headings_lower = "\n".join(_siyuan_headings).lower()
        content_lower = _siyuan_full_content.lower()

        for name, pattern in section_patterns.items():
            if re.search(pattern, headings_lower, re.IGNORECASE) or \
               re.search(pattern, content_lower, re.IGNORECASE):
                found_sections.append(name)
            else:
                missing_sections.append(name)

        passed = len(missing_sections) == 0
        detail = f"found={found_sections}"
        if missing_sections:
            detail += f", missing={missing_sections}"
        detail += f", headings={_siyuan_headings[:8]}"
        check("8. SiYuan: all 4 required sections", 2, passed, detail)
    except Exception as e:
        check("8. SiYuan: all 4 required sections", 2, False, f"exception: {e}")


def check_9_siyuan_introduction_detail() -> None:
    """Introduction section sets context with sufficient detail (>=120 chars)."""
    if not _siyuan_doc_id:
        check("9. SiYuan: detailed introduction", 1, False, "skipped: doc not found")
        return
    try:
        blocks = siyuan_sql(
            f"SELECT type, content, markdown FROM blocks "
            f"WHERE root_id = '{_siyuan_doc_id}' AND type != 'd' ORDER BY sort"
        )
        intro_text = ""
        in_intro = False
        for b in (blocks or []):
            btype = b.get("type", "")
            content = b.get("content", "")
            if btype == "h" and re.search(r"(导言|introduction|intro|背景|context)", content, re.IGNORECASE):
                in_intro = True
                continue
            if in_intro and btype == "h":
                break
            if in_intro:
                intro_text += content + " "

        if not in_intro:
            all_content = " ".join(b.get("content", "") for b in (blocks or [])[:5])
            intro_text = all_content

        intro_len = len(intro_text.strip())
        passed = intro_len >= 120
        check("9. SiYuan: detailed introduction", 1, passed,
              f"intro_length={intro_len}")
    except Exception as e:
        check("9. SiYuan: detailed introduction", 1, False, f"exception: {e}")


def check_10_siyuan_content_quality() -> None:
    """SiYuan EP-44 contains structured difference analysis, creator-intent, and version recommendation."""
    if not _siyuan_full_content:
        check("10. SiYuan: full content quality", 3, False,
              "skipped: SiYuan doc empty or not found")
        return
    try:
        passed, answer = llm_judge(
            _siyuan_full_content[:4000],
            "The document titled 'EP-44' about the Valley of Fear / Game of Shadows "
            "contains ALL of the following: "
            "(1) a detailed introduction setting the context of Conan Doyle's novel vs Ritchie's film, "
            "(2) a structured difference analysis listing specific book-film differences, "
            "(3) a creator-intent section discussing Doyle's and/or Ritchie's artistic goals, "
            "(4) an explicit version recommendation stating which medium (novel or film) "
            "is recommended and why — a vague 'both have merit' is NOT acceptable."
        )
        check("10. SiYuan: full content quality", 3, passed,
              f"llm_judge={answer}")
    except Exception as e:
        check("10. SiYuan: full content quality", 3, False, f"exception: {e}")


def check_11_siyuan_cross_app_links() -> None:
    """SiYuan EP-44 contains inline links/citations referencing Watcharr review and Booklore notes."""
    if not _siyuan_doc_id:
        check("11. SiYuan: cross-app inline links", 2, False,
              "skipped: doc not found")
        return
    try:
        combined = _siyuan_full_markdown + "\n" + _siyuan_full_content

        link_indicators = [
            r'\(\(.*?\)\)',
            r'siyuan://blocks/',
            r'watcharr',
            r'booklore',
            r'https?://[^\s)]+',
            r'\[.*?\]\(.*?\)',
        ]

        watcharr_ref = bool(re.search(
            r'(watcharr|game.?of.?shadows|sherlock|tracker|review)', combined, re.IGNORECASE
        ))
        booklore_ref = bool(re.search(
            r'(booklore|valley.?of.?fear|reading.?note|book.?note|classics)', combined, re.IGNORECASE
        ))

        has_link_syntax = False
        for pattern in link_indicators:
            if re.search(pattern, combined):
                has_link_syntax = True
                break

        passed = watcharr_ref and booklore_ref
        detail_parts = []
        if watcharr_ref:
            detail_parts.append("watcharr_ref=YES")
        else:
            detail_parts.append("watcharr_ref=NO")
        if booklore_ref:
            detail_parts.append("booklore_ref=YES")
        else:
            detail_parts.append("booklore_ref=NO")
        detail_parts.append(f"link_syntax={'YES' if has_link_syntax else 'NO'}")

        check("11. SiYuan: cross-app inline links", 2, passed,
              ", ".join(detail_parts))
    except Exception as e:
        check("11. SiYuan: cross-app inline links", 2, False, f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_1_watcharr_film_exists()
    check_2_watcharr_status_rating()
    check_3_watcharr_review_moriarty()
    check_4_booklore_book_exists()
    check_5_booklore_notes_exist()
    check_6_booklore_notes_dimensions()
    check_7_siyuan_doc_exists()
    check_8_siyuan_four_sections()
    check_9_siyuan_introduction_detail()
    check_10_siyuan_content_quality()
    check_11_siyuan_cross_app_links()

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
