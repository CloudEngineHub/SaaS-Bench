"""
Verifier for media_016: PDF paper → SiYuan structured research notes.

Checks: 10 weighted checks (20 total points) across siyuan.
Strategy: SiYuan REST API (SQL + notebook listing); llm_judge for content quality.

Required env vars:
  SERVER_HOSTNAME, SIYUAN_PORT, SIYUAN_CONTAINER.
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

SIYUAN_PORT = os.getenv("SIYUAN_PORT")
SIYUAN_CONTAINER = os.getenv("SIYUAN_CONTAINER")

for _var_name, _var_val in [
    ("SIYUAN_PORT", SIYUAN_PORT),
    ("SIYUAN_CONTAINER", SIYUAN_CONTAINER),
]:
    if not _var_val:
        print(f"FATAL: {_var_name} not set", file=sys.stderr)
        sys.exit(1)

SIYUAN_API = f"http://{HOST}:{SIYUAN_PORT}"
SIYUAN_TOKEN = ""

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


def siyuan_api_call(endpoint: str, payload: dict = None) -> dict:
    data = json.dumps(payload or {}).encode()
    headers = {"Content-Type": "application/json"}
    token = get_siyuan_token()
    if token:
        headers["Authorization"] = f"Token {token}"
    req = urllib.request.Request(
        f"{SIYUAN_API}{endpoint}",
        data=data,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


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


# ── Cached state ──────────────────────────────────────────────────────────────
_input_files_ok: bool = False
_doc_root_id: str = ""
_doc_notebook_id: str = ""
_sections: dict[str, str] = {}
_headings: list[str] = []


# ── Individual checks ─────────────────────────────────────────────────────────
def check_0_input_files_exist() -> None:
    global _input_files_ok
    missing = [p for p in INPUT_FILES if not os.path.isfile(p)]
    if missing:
        check("0. input_files_exist", 1, False, "missing: " + ", ".join(missing))
    else:
        _input_files_ok = True
        check("0. input_files_exist", 1, True)


def check_1_academic_sources_notebook() -> None:
    try:
        nb_result = siyuan_api_call("/api/notebook/lsNotebooks")
        notebooks = nb_result.get("data", {}).get("notebooks", [])
        found = None
        for nb in notebooks:
            name = (nb.get("name") or "").lower()
            if "academic" in name and "source" in name:
                found = nb
                break
        if found:
            check("1. academic_sources_notebook", 2, True,
                  f"notebook: '{found['name']}'")
        else:
            nb_names = [nb.get("name", "") for nb in notebooks]
            check("1. academic_sources_notebook", 2, False,
                  f"no 'Academic Sources' notebook; found: {nb_names[:10]}")
    except Exception as e:
        check("1. academic_sources_notebook", 2, False, f"exception: {e}")


def check_2_document_exists() -> None:
    global _doc_root_id, _doc_notebook_id
    try:
        rows = siyuan_sql(
            "SELECT id, content, box FROM blocks WHERE type = 'd' "
            "AND (content LIKE '%Research%Collaborative IR%' "
            "OR content LIKE '%Research:%Collaborative%IR%' "
            "OR content LIKE '%research%collaborative ir%') "
            "LIMIT 10;"
        )
        matched = None
        for r in rows:
            c = (r.get("content") or "").lower()
            if "research" in c and "collaborative ir" in c:
                matched = r
                break
        if not matched:
            rows2 = siyuan_sql(
                "SELECT id, content, box FROM blocks WHERE type = 'd' "
                "AND content LIKE '%Collaborative%IR%' LIMIT 10;"
            )
            for r in rows2:
                c = (r.get("content") or "").lower()
                if "collaborative ir" in c:
                    matched = r
                    break
        if matched:
            _doc_root_id = matched["id"]
            _doc_notebook_id = matched.get("box", "")
            check("2. document_exists", 2, True,
                  f"doc: '{matched.get('content', '')[:80]}'")
        else:
            check("2. document_exists", 2, False,
                  "no document matching 'Research: Collaborative IR' found")
    except Exception as e:
        check("2. document_exists", 2, False, f"exception: {e}")


def _load_doc_structure() -> None:
    global _sections, _headings
    if not _doc_root_id or _headings:
        return
    try:
        rows = siyuan_sql(
            f"SELECT content, type, markdown, subtype FROM blocks "
            f"WHERE root_id = '{_doc_root_id}' "
            f"AND type IN ('h', 'p', 'l', 'i') ORDER BY sort ASC;"
        )
        current_section = None
        for b in rows:
            content = b.get("content", "")
            btype = b.get("type", "")
            subtype = b.get("subtype", "")
            if btype == "h":
                _headings.append(content)
                c_lower = content.lower()
                if "abstract" in c_lower and "summary" in c_lower:
                    current_section = "abstract_summary"
                elif "core" in c_lower and "argument" in c_lower:
                    current_section = "core_arguments"
                elif "podcast" in c_lower and "integration" in c_lower:
                    current_section = "podcast_integration"
                elif "integration" in c_lower and "idea" in c_lower:
                    current_section = "podcast_integration"
                else:
                    current_section = None
                if current_section and current_section not in _sections:
                    _sections[current_section] = ""
            elif current_section and current_section in _sections:
                md = b.get("markdown", "") or content
                _sections[current_section] += md + "\n"
    except Exception:
        pass


def check_3_h2_abstract_summary() -> None:
    try:
        if not _doc_root_id:
            check("3. h2_abstract_summary", 2, False, "document not found")
            return
        rows = siyuan_sql(
            f"SELECT content, subtype FROM blocks "
            f"WHERE root_id = '{_doc_root_id}' AND type = 'h' ORDER BY sort;"
        )
        found = False
        for r in rows:
            c = (r.get("content") or "").lower()
            sub = r.get("subtype", "")
            if "abstract" in c and "summary" in c:
                if sub == "h2" or not sub:
                    found = True
                    break
        if found:
            check("3. h2_abstract_summary", 2, True)
        else:
            headings = [(r.get("content", ""), r.get("subtype", "")) for r in rows]
            check("3. h2_abstract_summary", 2, False,
                  f"no H2 'Abstract Summary' heading; headings: {headings[:8]}")
    except Exception as e:
        check("3. h2_abstract_summary", 2, False, f"exception: {e}")


def check_4_h2_core_arguments() -> None:
    try:
        if not _doc_root_id:
            check("4. h2_core_arguments", 2, False, "document not found")
            return
        rows = siyuan_sql(
            f"SELECT content, subtype FROM blocks "
            f"WHERE root_id = '{_doc_root_id}' AND type = 'h' ORDER BY sort;"
        )
        found = False
        for r in rows:
            c = (r.get("content") or "").lower()
            sub = r.get("subtype", "")
            if "core" in c and "argument" in c:
                if sub == "h2" or not sub:
                    found = True
                    break
        if found:
            check("4. h2_core_arguments", 2, True)
        else:
            headings = [(r.get("content", ""), r.get("subtype", "")) for r in rows]
            check("4. h2_core_arguments", 2, False,
                  f"no H2 'Core Arguments' heading; headings: {headings[:8]}")
    except Exception as e:
        check("4. h2_core_arguments", 2, False, f"exception: {e}")


def check_5_h2_podcast_integration() -> None:
    try:
        if not _doc_root_id:
            check("5. h2_podcast_integration", 2, False, "document not found")
            return
        rows = siyuan_sql(
            f"SELECT content, subtype FROM blocks "
            f"WHERE root_id = '{_doc_root_id}' AND type = 'h' ORDER BY sort;"
        )
        found = False
        for r in rows:
            c = (r.get("content") or "").lower()
            sub = r.get("subtype", "")
            if ("podcast" in c and "integration" in c) or \
               ("integration" in c and "idea" in c):
                if sub == "h2" or not sub:
                    found = True
                    break
        if found:
            check("5. h2_podcast_integration", 2, True)
        else:
            headings = [(r.get("content", ""), r.get("subtype", "")) for r in rows]
            check("5. h2_podcast_integration", 2, False,
                  f"no H2 'Podcast Integration Ideas' heading; headings: {headings[:8]}")
    except Exception as e:
        check("5. h2_podcast_integration", 2, False, f"exception: {e}")


def check_6_abstract_summary_content() -> None:
    try:
        if not _doc_root_id:
            check("6. abstract_summary_content", 2, False, "document not found")
            return
        _load_doc_structure()
        abstract = _sections.get("abstract_summary", "")
        char_count = len(abstract.strip())
        if char_count >= 100:
            check("6. abstract_summary_content", 2, True,
                  f"{char_count} chars")
        else:
            check("6. abstract_summary_content", 2, False,
                  f"abstract summary too short: {char_count} chars (need ≥100)")
    except Exception as e:
        check("6. abstract_summary_content", 2, False, f"exception: {e}")


def check_7_core_arguments_bullets() -> None:
    try:
        if not _doc_root_id:
            check("7. core_arguments_≥3_bullets", 2, False, "document not found")
            return
        _load_doc_structure()
        core_text = _sections.get("core_arguments", "")
        bullets = [
            line.strip() for line in core_text.split("\n")
            if line.strip() and (
                line.strip().startswith("- ") or
                line.strip().startswith("* ") or
                line.strip().startswith("+ ") or
                re.match(r"^\d+[\.\)]\s", line.strip())
            )
        ]
        if not bullets:
            rows = siyuan_sql(
                f"SELECT id FROM blocks WHERE root_id = '{_doc_root_id}' "
                f"AND type = 'i' ORDER BY sort;"
            )
            heading_rows = siyuan_sql(
                f"SELECT id, content FROM blocks WHERE root_id = '{_doc_root_id}' "
                f"AND type = 'h' ORDER BY sort;"
            )
            core_heading_id = None
            next_heading_sort = None
            for i, h in enumerate(heading_rows):
                c = (h.get("content") or "").lower()
                if "core" in c and "argument" in c:
                    core_heading_id = h["id"]
                    break

            if core_heading_id:
                all_blocks = siyuan_sql(
                    f"SELECT type, content FROM blocks WHERE root_id = '{_doc_root_id}' "
                    f"AND type = 'i' ORDER BY sort;"
                )
                bullet_count = len(all_blocks)
            else:
                bullet_count = 0
        else:
            bullet_count = len(bullets)

        if bullet_count >= 3:
            check("7. core_arguments_≥3_bullets", 2, True,
                  f"{bullet_count} bullet points found")
        else:
            check("7. core_arguments_≥3_bullets", 2, False,
                  f"found {bullet_count} bullets, need ≥3")
    except Exception as e:
        check("7. core_arguments_≥3_bullets", 2, False, f"exception: {e}")


def check_8_podcast_integration_2_ideas() -> None:
    try:
        if not _doc_root_id:
            check("8. podcast_integration_2_ideas", 2, False, "document not found")
            return
        _load_doc_structure()
        podcast_text = _sections.get("podcast_integration", "")
        ideas = [
            line.strip() for line in podcast_text.split("\n")
            if line.strip() and (
                line.strip().startswith("- ") or
                line.strip().startswith("* ") or
                line.strip().startswith("+ ") or
                re.match(r"^\d+[\.\)]\s", line.strip())
            )
        ]
        if not ideas:
            paragraphs = [
                p.strip() for p in podcast_text.split("\n")
                if p.strip() and len(p.strip()) > 20
            ]
            idea_count = len(paragraphs)
        else:
            idea_count = len(ideas)

        if idea_count >= 2:
            check("8. podcast_integration_2_ideas", 2, True,
                  f"{idea_count} ideas found")
        else:
            check("8. podcast_integration_2_ideas", 2, False,
                  f"found {idea_count} ideas, need ≥2")
    except Exception as e:
        check("8. podcast_integration_2_ideas", 2, False, f"exception: {e}")


def check_9_cross_modal_pdf_consistency() -> None:
    try:
        if not _input_files_ok:
            check("9. cross_modal_pdf_consistency", 3, False,
                  "skipped: input file missing")
            return
        if not _doc_root_id:
            check("9. cross_modal_pdf_consistency", 3, False,
                  "skipped: document not found")
            return
        _load_doc_structure()
        abstract = _sections.get("abstract_summary", "")
        core = _sections.get("core_arguments", "")
        doc_content = (abstract + "\n" + core).strip()
        if len(doc_content) < 50:
            check("9. cross_modal_pdf_consistency", 3, False,
                  "document content too short for cross-modal check")
            return
        condition = (
            "The document content is a substantive summary and analysis of a research paper "
            "about Collaborative Knowledge Creation and Management in Information Retrieval. "
            "The abstract summary accurately reflects themes of collaborative IR, knowledge "
            "creation, or information retrieval research. The core arguments are relevant to "
            "the academic paper's subject matter, not generic filler."
        )
        passed, raw = llm_judge(doc_content[:3000], condition)
        check("9. cross_modal_pdf_consistency", 3, passed, f"llm_judge: {raw}")
    except Exception as e:
        check("9. cross_modal_pdf_consistency", 3, False, f"exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    check_0_input_files_exist()
    check_1_academic_sources_notebook()
    check_2_document_exists()
    check_3_h2_abstract_summary()
    check_4_h2_core_arguments()
    check_5_h2_podcast_integration()
    check_6_abstract_summary_content()
    check_7_core_arguments_bullets()
    check_8_podcast_integration_2_ideas()
    check_9_cross_modal_pdf_consistency()

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
