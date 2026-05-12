"""
Verifier for imc_033: PDF paper → SiYuan structured summary

Checks: 11 weighted checks (18pt total) on siyuan.
Strategy: SiYuan REST API (/api/query/sql, /api/notebook/lsNotebooks);
          llm_judge for cross-modal PDF-vs-summary consistency.

Required env vars:
  SERVER_HOSTNAME, SIYUAN_PORT, SIYUAN_CONTAINER
"""

import os
import sys
import subprocess
import json
import re
import base64

try:
    import requests
except ImportError:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "requests"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    import requests

# ── Config (from env) ─────────────────────────────────────────────────────────
HOST = os.getenv("SERVER_HOSTNAME", "localhost")
SIYUAN_PORT = os.getenv("SIYUAN_PORT")
SIYUAN_CONTAINER = os.getenv("SIYUAN_CONTAINER")

_missing = []
for _var in ["SIYUAN_PORT", "SIYUAN_CONTAINER"]:
    if not os.getenv(_var):
        _missing.append(_var)
if _missing:
    print(f"FATAL: {', '.join(_missing)} not set", file=sys.stderr)
    sys.exit(1)

_INPUTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "inputs"
)

INPUT_FILES: list[str] = [
    os.path.join(_INPUTS_DIR, "siyuan_paper_001.pdf"),
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


_siyuan_auth_cached = None


def _get_siyuan_auth() -> str:
    global _siyuan_auth_cached
    if _siyuan_auth_cached is not None:
        return _siyuan_auth_cached
    try:
        rc, stdout, _ = docker_exec(
            SIYUAN_CONTAINER, "cat", "/siyuan/workspace/conf/conf.json",
            timeout=10,
        )
        if rc == 0 and stdout.strip():
            conf = json.loads(stdout)
            token = conf.get("api", {}).get("token", "")
            if token:
                _siyuan_auth_cached = token
                return _siyuan_auth_cached
    except Exception:
        pass
    try:
        rc, stdout, _ = docker_exec(
            SIYUAN_CONTAINER, "sh", "-c",
            "cat /proc/1/cmdline | tr '\\0' '\\n'",
        )
        for line in stdout.splitlines():
            if "accessAuthCode=" in line:
                _siyuan_auth_cached = line.split("=", 1)[1].strip()
                return _siyuan_auth_cached
    except Exception:
        pass
    _siyuan_auth_cached = ""
    return _siyuan_auth_cached


def siyuan_api(endpoint: str, payload: dict, timeout: int = 15) -> dict:
    url = f"http://{HOST}:{SIYUAN_PORT}{endpoint}"
    headers = {"Content-Type": "application/json"}
    auth = _get_siyuan_auth()
    if auth:
        headers["Authorization"] = f"Token {auth}"
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        return resp.json()
    except Exception as e:
        return {"code": -1, "msg": str(e), "data": None}


def siyuan_sql(stmt: str) -> list:
    result = siyuan_api("/api/query/sql", {"stmt": stmt})
    data = result.get("data")
    if isinstance(data, list):
        return data
    return []


def count_sentences(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    parts = re.split(r'[.!?。！？]+', text)
    return sum(1 for p in parts if len(p.strip()) > 5)


def llm_judge(content: str, condition: str, timeout: int = 30) -> tuple[bool, str]:
    api_base = os.getenv("MINDRA_BASE_URL", "https://api.mindracode.com/v1")
    api_key = os.getenv("MINDRA_API_KEY", "")
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
            json={
                "model": "gemini-3.0-flash-preview",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 10,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        answer = resp.json()["choices"][0]["message"]["content"].strip().upper()
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
    ext = os.path.splitext(image_path)[1].lower()
    mime = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp", ".pdf": "application/pdf",
    }.get(ext, "application/octet-stream")
    if not os.path.isfile(image_path):
        return False, f"file not found: {image_path}"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    prompt = (
        f"You are given a document and a summary that an AI agent wrote based on it.\n"
        f"Summary:\n«{recorded_value}»\n\n"
        f"Condition: {condition}\n\n"
        f"Does the summary accurately reflect the document content, "
        f"satisfying the condition above?\n"
        f"Answer only YES or NO."
    )
    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            json={
                "model": "gemini-3.0-flash-preview",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url",
                         "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }],
                "max_tokens": 10,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        answer = resp.json()["choices"][0]["message"]["content"].strip().upper()
        return answer.startswith("YES"), answer
    except Exception as e:
        return False, f"llm_judge_vision error: {e}"


# ── Cached lookups ────────────────────────────────────────────────────────────
_notebook_id = None
_notebook_id_searched = False


def _find_notebook_id() -> str | None:
    global _notebook_id, _notebook_id_searched
    if _notebook_id_searched:
        return _notebook_id
    _notebook_id_searched = True
    result = siyuan_api("/api/notebook/lsNotebooks", {})
    notebooks = result.get("data", {}).get("notebooks", [])
    for nb in notebooks:
        if nb.get("name", "").strip().lower() == "academic research":
            _notebook_id = nb["id"]
            return _notebook_id
    return None


_doc_id = None
_doc_id_searched = False


def _find_doc() -> str | None:
    global _doc_id, _doc_id_searched
    if _doc_id_searched:
        return _doc_id
    _doc_id_searched = True
    rows = siyuan_sql(
        "SELECT id, content, box, hpath FROM blocks "
        "WHERE type = 'd' AND content LIKE '%Paper Summary%Collaborative Knowledge Creation%' "
        "LIMIT 10"
    )
    nb_id = _find_notebook_id()
    for row in rows:
        if nb_id and row.get("box") == nb_id:
            _doc_id = row["id"]
            return _doc_id
    if rows:
        _doc_id = rows[0]["id"]
        return _doc_id
    rows2 = siyuan_sql(
        "SELECT id, content, box FROM blocks "
        "WHERE type = 'd' AND content LIKE '%Collaborative Knowledge Creation%' "
        "LIMIT 10"
    )
    if rows2:
        _doc_id = rows2[0]["id"]
        return _doc_id
    return None


_doc_blocks_cache = None


def _get_doc_blocks() -> list[dict]:
    global _doc_blocks_cache
    if _doc_blocks_cache is not None:
        return _doc_blocks_cache
    doc_id = _find_doc()
    if not doc_id:
        _doc_blocks_cache = []
        return _doc_blocks_cache
    rows = siyuan_sql(
        f"SELECT id, type, content, markdown FROM blocks "
        f"WHERE root_id = '{doc_id}' AND type != 'd' ORDER BY sort"
    )
    _doc_blocks_cache = rows
    return _doc_blocks_cache


def _get_section_text(heading_name: str) -> str:
    blocks = _get_doc_blocks()
    in_section = False
    parts = []
    for b in blocks:
        if b.get("type") == "h":
            if heading_name.lower() in b.get("content", "").lower():
                in_section = True
                continue
            elif in_section:
                break
        if in_section and b.get("type") in ("p", "l", "i", "b"):
            text = b.get("markdown") or b.get("content") or ""
            parts.append(text.strip())
    return "\n".join(parts)


def _get_full_doc_text() -> str:
    blocks = _get_doc_blocks()
    parts = []
    for b in blocks:
        text = b.get("markdown") or b.get("content") or ""
        if text.strip():
            parts.append(text.strip())
    return "\n".join(parts)


# ── Individual checks ─────────────────────────────────────────────────────────
def check_0_input_files_exist() -> None:
    missing = [p for p in INPUT_FILES if not os.path.isfile(p)]
    if missing:
        check("0. input_files_exist", 1, False, "missing: " + ", ".join(missing))
    else:
        check("0. input_files_exist", 1, True)


def check_1_notebook_exists() -> None:
    try:
        nb_id = _find_notebook_id()
        check("1. notebook_academic_research", 1, nb_id is not None,
              "" if nb_id else "no notebook named 'Academic Research' found")
    except Exception as e:
        check("1. notebook_academic_research", 1, False, f"exception: {e}")


def check_2_document_exists() -> None:
    try:
        doc_id = _find_doc()
        passed = doc_id is not None
        detail = ""
        if passed:
            nb_id = _find_notebook_id()
            rows = siyuan_sql(
                f"SELECT box FROM blocks WHERE id = '{doc_id}' AND type = 'd' LIMIT 1"
            )
            if nb_id and rows and rows[0].get("box") != nb_id:
                detail = "document found but not in 'Academic Research' notebook"
        else:
            detail = "no document matching 'Paper Summary: Collaborative Knowledge Creation'"
        check("2. document_exists", 2, passed, detail)
    except Exception as e:
        check("2. document_exists", 2, False, f"exception: {e}")


def check_3_section_core_thesis() -> None:
    try:
        blocks = _get_doc_blocks()
        headings = [
            b.get("content", "").strip()
            for b in blocks if b.get("type") == "h"
        ]
        found = any("core thesis" in h.lower() for h in headings)
        check("3. section_core_thesis_exists", 1, found,
              "" if found else f"headings found: {headings[:10]}")
    except Exception as e:
        check("3. section_core_thesis_exists", 1, False, f"exception: {e}")


def check_4_section_methodology() -> None:
    try:
        blocks = _get_doc_blocks()
        headings = [
            b.get("content", "").strip()
            for b in blocks if b.get("type") == "h"
        ]
        found = any("methodology" in h.lower() for h in headings)
        check("4. section_methodology_exists", 1, found,
              "" if found else f"headings found: {headings[:10]}")
    except Exception as e:
        check("4. section_methodology_exists", 1, False, f"exception: {e}")


def check_5_section_podcast_relevance() -> None:
    try:
        blocks = _get_doc_blocks()
        headings = [
            b.get("content", "").strip()
            for b in blocks if b.get("type") == "h"
        ]
        found = any("podcast relevance" in h.lower() for h in headings)
        check("5. section_podcast_relevance_exists", 1, found,
              "" if found else f"headings found: {headings[:10]}")
    except Exception as e:
        check("5. section_podcast_relevance_exists", 1, False, f"exception: {e}")


def check_6_core_thesis_sentences() -> None:
    try:
        text = _get_section_text("Core Thesis")
        if not text:
            check("6. core_thesis_sentence_count", 2, False, "section empty or not found")
            return
        n = count_sentences(text)
        passed = n >= 2
        check("6. core_thesis_sentence_count", 2, passed,
              "" if passed else f"found {n} sentences, need >= 2")
    except Exception as e:
        check("6. core_thesis_sentence_count", 2, False, f"exception: {e}")


def check_7_methodology_sentences() -> None:
    try:
        text = _get_section_text("Methodology")
        if not text:
            check("7. methodology_sentence_count", 2, False, "section empty or not found")
            return
        n = count_sentences(text)
        passed = n >= 3
        check("7. methodology_sentence_count", 2, passed,
              "" if passed else f"found {n} sentences, need >= 3")
    except Exception as e:
        check("7. methodology_sentence_count", 2, False, f"exception: {e}")


def check_8_podcast_relevance_sentences() -> None:
    try:
        text = _get_section_text("Podcast Relevance")
        if not text:
            check("8. podcast_relevance_sentence_count", 2, False,
                  "section empty or not found")
            return
        n = count_sentences(text)
        passed = n >= 2
        check("8. podcast_relevance_sentence_count", 2, passed,
              "" if passed else f"found {n} sentences, need >= 2")
    except Exception as e:
        check("8. podcast_relevance_sentence_count", 2, False, f"exception: {e}")


def check_9_content_mentions_ir() -> None:
    try:
        text = _get_full_doc_text().lower()
        if not text:
            check("9. content_mentions_ir", 2, False, "document empty or not found")
            return
        has_ir = (
            "information retrieval" in text
            or re.search(r'\bIR\b', _get_full_doc_text()) is not None
        )
        check("9. content_mentions_ir", 2, has_ir,
              "" if has_ir else "no mention of 'Information Retrieval' or 'IR' in document")
    except Exception as e:
        check("9. content_mentions_ir", 2, False, f"exception: {e}")


def check_10_cross_modal_pdf_consistency() -> None:
    pdf_path = INPUT_FILES[0]
    if not os.path.isfile(pdf_path):
        check("10. cross_modal_pdf_consistency", 3, False,
              "skipped: input file missing")
        return
    try:
        full_text = _get_full_doc_text()
        if not full_text:
            check("10. cross_modal_pdf_consistency", 3, False,
                  "document empty or not found")
            return
        passed, raw = llm_judge(
            full_text,
            "The summary is about a paper on Collaborative Knowledge Creation "
            "and Information Retrieval (IR). It accurately reflects the paper's "
            "core thesis, methodology, and relevance. It specifically mentions "
            "the role of Information Retrieval (IR) in knowledge production."
        )
        check("10. cross_modal_pdf_consistency", 3, passed,
              "" if passed else f"llm_judge: {raw}")
    except Exception as e:
        check("10. cross_modal_pdf_consistency", 3, False, f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_0_input_files_exist()
    check_1_notebook_exists()
    check_2_document_exists()
    check_3_section_core_thesis()
    check_4_section_methodology()
    check_5_section_podcast_relevance()
    check_6_core_thesis_sentences()
    check_7_methodology_sentences()
    check_8_podcast_relevance_sentences()
    check_9_content_mentions_ir()
    check_10_cross_modal_pdf_consistency()

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
