"""
Verifier for media_063: Add ballads book to Booklore, create SiYuan research note with link.

Checks: 8 weighted checks across booklore, siyuan.
Strategy: docker exec MariaDB for booklore; REST API for siyuan.

Required env vars:
  SERVER_HOSTNAME, BOOKLORE_PORT, BOOKLORE_CONTAINER, SIYUAN_PORT, SIYUAN_CONTAINER
"""

import os
import sys
import json
import subprocess
import re
import requests

# ── Config (from env) ─────────────────────────────────────────────────────────
HOST = os.getenv("SERVER_HOSTNAME", "localhost")

BOOKLORE_PORT = os.getenv("BOOKLORE_PORT")
BOOKLORE_CONTAINER = os.getenv("BOOKLORE_CONTAINER")
SIYUAN_PORT = os.getenv("SIYUAN_PORT")
SIYUAN_CONTAINER = os.getenv("SIYUAN_CONTAINER")

for var_name, var_val in [
    ("BOOKLORE_PORT", BOOKLORE_PORT),
    ("BOOKLORE_CONTAINER", BOOKLORE_CONTAINER),
    ("SIYUAN_PORT", SIYUAN_PORT),
    ("SIYUAN_CONTAINER", SIYUAN_CONTAINER),
]:
    if not var_val:
        print(f"FATAL: {var_name} not set", file=sys.stderr)
        sys.exit(1)

BOOKLORE_DB_CONTAINER = os.getenv("BOOKLORE_DB_CONTAINER", BOOKLORE_CONTAINER + "-db")
BOOKLORE_BASE = f"http://{HOST}:{BOOKLORE_PORT}"
SIYUAN_BASE = f"http://{HOST}:{SIYUAN_PORT}"


def _get_siyuan_token() -> str:
    try:
        r = subprocess.run(
            ["docker", "exec", SIYUAN_CONTAINER, "cat",
             "/siyuan/workspace/conf/conf.json"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            conf = json.loads(r.stdout)
            return conf.get("api", {}).get("token", "")
    except Exception:
        pass
    return ""


SIYUAN_TOKEN = _get_siyuan_token()

# ── Result accumulator ────────────────────────────────────────────────────────
_checks: list[tuple[str, int, bool, str]] = []


def check(label: str, weight: int, passed: bool, detail: str = "") -> None:
    _checks.append((label, weight, passed, detail))
    status = "PASS" if passed else "FAIL"
    tail = f"  ({detail})" if detail else ""
    print(f"[{status}] ({weight}pt) {label}{tail}", file=sys.stderr)


# ── Helpers ───────────────────────────────────────────────────────────────────
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


def _siyuan_headers() -> dict:
    h = {"Content-Type": "application/json"}
    if SIYUAN_TOKEN:
        h["Authorization"] = f"Token {SIYUAN_TOKEN}"
    return h


def siyuan_sql(stmt: str) -> list:
    try:
        resp = requests.post(
            f"{SIYUAN_BASE}/api/query/sql",
            headers=_siyuan_headers(),
            json={"stmt": stmt},
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("code", -1) != 0:
            print(f"  siyuan_sql non-zero code: {body.get('msg')}", file=sys.stderr)
            return []
        data = body.get("data", [])
        return data if data else []
    except Exception as e:
        print(f"  siyuan_sql error: {e}", file=sys.stderr)
        return []


def siyuan_api(endpoint: str, payload: dict) -> dict:
    try:
        resp = requests.post(
            f"{SIYUAN_BASE}{endpoint}",
            headers=_siyuan_headers(),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  siyuan_api error: {e}", file=sys.stderr)
        return {}


# ── Individual checks ─────────────────────────────────────────────────────────

_book_id: str | None = None


def check_1_book_exists() -> None:
    global _book_id
    try:
        q = (
            "SELECT bm.book_id, bm.title FROM book_metadata bm "
            "WHERE bm.title LIKE '%Old Ballads%' AND bm.title LIKE '%Volume 4%' "
            "LIMIT 1"
        )
        result = mariadb_query(q)
        if result:
            parts = result.split("\t", 1)
            _book_id = parts[0]
            title = parts[1] if len(parts) > 1 else ""
            check("1. Book 'A Book of Old Ballads — Volume 4' exists", 1, True,
                  f"book_id={_book_id}, title={title}")
        else:
            q_broad = (
                "SELECT bm.book_id, bm.title FROM book_metadata bm "
                "WHERE bm.title LIKE '%Ballad%' LIMIT 5"
            )
            broad = mariadb_query(q_broad)
            check("1. Book 'A Book of Old Ballads — Volume 4' exists", 1, False,
                  f"not found; ballad titles: {broad[:200]}")
    except Exception as e:
        check("1. Book 'A Book of Old Ballads — Volume 4' exists", 1, False,
              f"exception: {e}")


def check_2_read_status() -> None:
    if not _book_id:
        check("2. Book status is 'Want to Read'", 2, False, "skipped: book not found")
        return
    try:
        q_book = f"SELECT read_status FROM books WHERE id = {_book_id}"
        status_book = mariadb_query(q_book).strip()

        q_progress = (
            f"SELECT read_status FROM user_book_progress "
            f"WHERE book_id = {_book_id} LIMIT 1"
        )
        status_progress = mariadb_query(q_progress).strip()

        q_shelf = (
            f"SELECT s.name FROM shelf s "
            f"JOIN book_shelf_mapping bsm ON s.id = bsm.shelf_id "
            f"WHERE bsm.book_id = {_book_id}"
        )
        shelves = mariadb_query(q_shelf)

        status = status_progress or status_book
        want_to_read = False
        detail_parts = []

        if status:
            detail_parts.append(f"read_status={status}")
            if status.upper() in ("UNREAD", "WANT_TO_READ"):
                want_to_read = True
        if shelves:
            detail_parts.append(f"shelves={shelves}")
            shelves_lower = shelves.lower()
            if "want" in shelves_lower and "read" in shelves_lower:
                want_to_read = True
            elif "to read" in shelves_lower or "to-read" in shelves_lower:
                want_to_read = True

        check("2. Book status is 'Want to Read'", 2, want_to_read,
              "; ".join(detail_parts) if detail_parts else "no status or shelf found")
    except Exception as e:
        check("2. Book status is 'Want to Read'", 2, False, f"exception: {e}")


def check_3_reading_note_oral_traditions() -> None:
    if not _book_id:
        check("3. Book has note mentioning 'Oral Traditions'", 2, False,
              "skipped: book not found")
        return
    try:
        q_v1 = (
            f"SELECT content FROM book_notes "
            f"WHERE book_id = {_book_id} "
            f"ORDER BY updated_at DESC LIMIT 5"
        )
        q_v2 = (
            f"SELECT note_content FROM book_notes_v2 "
            f"WHERE book_id = {_book_id} "
            f"ORDER BY created_at DESC LIMIT 5"
        )
        notes_v1 = mariadb_query(q_v1)
        notes_v2 = mariadb_query(q_v2)

        all_notes = (notes_v1 + " " + notes_v2).lower()
        has_oral = "oral tradition" in all_notes or "oral traditions" in all_notes

        if has_oral:
            check("3. Book has note mentioning 'Oral Traditions'", 2, True,
                  "found 'Oral Traditions' in note content")
        else:
            snippet_v1 = notes_v1[:150] if notes_v1 else "(none)"
            snippet_v2 = notes_v2[:150] if notes_v2 else "(none)"
            check("3. Book has note mentioning 'Oral Traditions'", 2, False,
                  f"'Oral Traditions' not found; v1={snippet_v1}; v2={snippet_v2}")
    except Exception as e:
        check("3. Book has note mentioning 'Oral Traditions'", 2, False,
              f"exception: {e}")


_notebook_id: str | None = None


def check_4_siyuan_podcast_scripts_notebook() -> None:
    global _notebook_id
    try:
        resp = siyuan_api("/api/notebook/lsNotebooks", {})
        notebooks = resp.get("data", {}).get("notebooks", [])
        for nb in notebooks:
            name = nb.get("name", "")
            if "podcast" in name.lower() and "script" in name.lower():
                _notebook_id = nb.get("id", "")
                check("4. SiYuan 'Podcast Scripts' notebook exists", 2, True,
                      f"notebook_id={_notebook_id}, name='{name}'")
                return

        names = [nb.get("name", "") for nb in notebooks]
        check("4. SiYuan 'Podcast Scripts' notebook exists", 2, False,
              f"not found; notebooks: {names}")
    except Exception as e:
        check("4. SiYuan 'Podcast Scripts' notebook exists", 2, False,
              f"exception: {e}")


_doc_id: str | None = None


def check_5_siyuan_doc_exists() -> None:
    global _doc_id
    try:
        rows = siyuan_sql(
            "SELECT id, content, box FROM blocks "
            "WHERE type = 'd' AND content LIKE '%EP-Research%Oral Traditions%'"
        )
        if not rows:
            rows = siyuan_sql(
                "SELECT id, content, box FROM blocks "
                "WHERE type = 'd' AND content LIKE '%Oral Traditions%'"
            )

        if rows:
            doc = rows[0]
            _doc_id = doc.get("id", "")
            title = doc.get("content", "")
            check("5. SiYuan doc 'EP-Research: Oral Traditions' exists", 2, True,
                  f"doc_id={_doc_id}, title='{title}'")
        else:
            all_docs = siyuan_sql(
                "SELECT content FROM blocks WHERE type = 'd' "
                "AND (content LIKE '%EP%' OR content LIKE '%Oral%' OR content LIKE '%Research%') "
                "LIMIT 5"
            )
            titles = [r.get("content", "") for r in (all_docs or [])]
            check("5. SiYuan doc 'EP-Research: Oral Traditions' exists", 2, False,
                  f"not found; related docs: {titles}")
    except Exception as e:
        check("5. SiYuan doc 'EP-Research: Oral Traditions' exists", 2, False,
              f"exception: {e}")


def check_6_doc_in_podcast_notebook() -> None:
    if not _doc_id:
        check("6. Doc is under 'Podcast Scripts' notebook", 1, False,
              "skipped: doc not found")
        return
    if not _notebook_id:
        check("6. Doc is under 'Podcast Scripts' notebook", 1, False,
              "skipped: notebook not found")
        return
    try:
        rows = siyuan_sql(
            f"SELECT box FROM blocks WHERE id = '{_doc_id}' AND type = 'd'"
        )
        if rows:
            box = rows[0].get("box", "")
            passed = box == _notebook_id
            check("6. Doc is under 'Podcast Scripts' notebook", 1, passed,
                  f"doc box={box}, expected notebook={_notebook_id}")
        else:
            check("6. Doc is under 'Podcast Scripts' notebook", 1, False,
                  "could not retrieve doc box")
    except Exception as e:
        check("6. Doc is under 'Podcast Scripts' notebook", 1, False,
              f"exception: {e}")


def check_7_siyuan_doc_mentions_book() -> None:
    if not _doc_id:
        check("7. SiYuan doc mentions the ballads book", 1, False,
              "skipped: doc not found")
        return
    try:
        blocks = siyuan_sql(
            f"SELECT content, markdown FROM blocks "
            f"WHERE root_id = '{_doc_id}' AND type != 'd'"
        )
        full_content = " ".join(
            (b.get("content", "") + " " + b.get("markdown", ""))
            for b in (blocks or [])
        ).lower()

        has_ballad = "ballad" in full_content or "old ballads" in full_content
        check("7. SiYuan doc mentions the ballads book", 1, has_ballad,
              "found 'ballad' reference" if has_ballad
              else f"'ballad' not in doc content (len={len(full_content)})")
    except Exception as e:
        check("7. SiYuan doc mentions the ballads book", 1, False,
              f"exception: {e}")


def check_8_siyuan_hyperlink_to_booklore() -> None:
    if not _doc_id:
        check("8. SiYuan doc has hyperlink to Booklore entry", 3, False,
              "skipped: doc not found")
        return
    try:
        blocks = siyuan_sql(
            f"SELECT markdown FROM blocks "
            f"WHERE root_id = '{_doc_id}' AND type != 'd'"
        )
        full_md = " ".join(b.get("markdown", "") for b in (blocks or []))

        booklore_port = BOOKLORE_PORT
        url_patterns = [
            rf"https?://[^\s\)\"'>]+:{re.escape(booklore_port)}[^\s\)\"'>]*",
            rf"https?://[^\s\)\"'>]*booklore[^\s\)\"'>]*",
            rf"https?://[^\s\)\"'>]+/book/[^\s\)\"'>]*",
            rf"https?://[^\s\)\"'>]+/books/[^\s\)\"'>]*",
            rf"https?://[^\s\)\"'>]+/api/v1/books/[^\s\)\"'>]*",
        ]
        all_urls = set()
        for pat in url_patterns:
            all_urls.update(re.findall(pat, full_md, re.IGNORECASE))

        md_links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', full_md)
        for text, url in md_links:
            url_lower = url.lower()
            if (f":{booklore_port}" in url or "booklore" in url_lower
                    or "/book/" in url_lower or "/books/" in url_lower):
                all_urls.add(url)

        href_links = re.findall(r'href=["\']([^"\']+)["\']', full_md)
        for url in href_links:
            url_lower = url.lower()
            if (f":{booklore_port}" in url or "booklore" in url_lower
                    or "/book/" in url_lower or "/books/" in url_lower):
                all_urls.add(url)

        if all_urls:
            check("8. SiYuan doc has hyperlink to Booklore entry", 3, True,
                  f"found {len(all_urls)} link(s): {list(all_urls)[:3]}")
        else:
            any_links = re.findall(r'https?://[^\s\)\">\'\]]+', full_md)
            check("8. SiYuan doc has hyperlink to Booklore entry", 3, False,
                  f"no Booklore links found; all URLs: {any_links[:5]}")
    except Exception as e:
        check("8. SiYuan doc has hyperlink to Booklore entry", 3, False,
              f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_1_book_exists()
    check_2_read_status()
    check_3_reading_note_oral_traditions()
    check_4_siyuan_podcast_scripts_notebook()
    check_5_siyuan_doc_exists()
    check_6_doc_in_podcast_notebook()
    check_7_siyuan_doc_mentions_book()
    check_8_siyuan_hyperlink_to_booklore()

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
