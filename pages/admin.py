"""
pages/admin.py
--------------
Admin panel with 4 tabs:
  1. Documents  – upload PDF / TXT / DOCX / MD (max 50 MB)
  2. Analytics  – usage stats, satisfaction, continual-learning metrics
  3. Logs       – last 20 decrypted audit log entries
  4. Scraper    – manual trigger + scraping activity
"""

import hashlib
import io
import json
import os
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from utils.tz import since_gmt5, utc_str_to_gmt5, now_gmt5_str
from typing import Dict, List, Optional, Tuple

import streamlit as st

st.set_page_config(
    page_title="AdaptIQ — Admin",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.responsive import inject_responsive_css

inject_responsive_css()

from utils.db_init import get_connection
from utils.db_lock import db_lock
from utils.encryption import decrypt
from pipeline.embeddings import embed_texts
from pipeline.retriever import add_chunks, get_or_create_collection
from continual_learning.drift_detector import drift_summary
from continual_learning.ewc import calculate_plasticity
from scraper.updater import run_update
from utils.pendo_track import track as pendo_track


# ── auth guard ────────────────────────────────────────────────────────────────


def _require_admin() -> bool:
    user = st.session_state.get("user")
    if not user or user.get("role") != "admin":
        st.error("Admin access required.")
        st.page_link("app.py", label="← Go to login")
        return False
    return True


# ── document ingestion ────────────────────────────────────────────────────────


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    chunks: List[str] = []
    start = 0
    while start < len(text):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def _extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    try:
        if ext == "txt" or ext == "md":
            return file_bytes.decode("utf-8", errors="replace")

        if ext == "pdf":
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for page in reader.pages:
                pages_text.append(page.extract_text() or "")
            return "\n\n".join(pages_text)

        if ext == "docx":
            import docx

            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

        return file_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        raise RuntimeError(f"Could not extract text from '{filename}': {exc}") from exc


def _ingest_document(
    file_bytes: bytes,
    filename: str,
    file_type: str,
    visibility: str,
    company_id: int,
    user_id: int,
) -> Tuple[bool, str]:
    """Parse, chunk, embed, and index a document. Returns (success, message)."""
    content_hash = hashlib.md5(file_bytes).hexdigest()
    file_size = len(file_bytes)

    try:
        text = _extract_text_from_file(file_bytes, filename)
    except RuntimeError as exc:
        return False, str(exc)

    if not text.strip():
        return False, "Document appears to be empty or unreadable."

    chunks = _chunk_text(text)
    if not chunks:
        return False, "No text chunks could be extracted."

    try:
        embeddings = embed_texts(chunks)
    except Exception as exc:
        return False, f"Embedding failed: {exc}"

    role = "user" if visibility == "public" else "worker"
    ids = [
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"{company_id}:{filename}:chunk{i}"))
        for i in range(len(chunks))
    ]
    metadatas = [
        {
            "source_file": filename,
            "page_num": i,
            "company_id": company_id,
            "website_url": "",
            "relevance_score": 1.0,
            "visibility": visibility,
            "usage_count": 0,
        }
        for i in range(len(chunks))
    ]

    try:
        add_chunks(company_id, role, ids, chunks, embeddings, metadatas)
    except Exception as exc:
        return False, f"ChromaDB insert failed: {exc}"

    # Persist document record in SQLite
    try:
        with db_lock():
            conn = get_connection()
            conn.execute(
                """INSERT INTO documents
                   (company_id, filename, file_type, file_size, visibility,
                    uploaded_by, content_hash, chunk_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    company_id,
                    filename,
                    file_type,
                    file_size,
                    visibility,
                    user_id,
                    content_hash,
                    len(chunks),
                ),
            )
            conn.commit()
            conn.close()
    except Exception as exc:
        return False, f"DB record failed: {exc}"

    return True, f"Indexed {len(chunks)} chunks from '{filename}'."


# ── analytics helpers ─────────────────────────────────────────────────────────


def _get_request_counts(company_id: int) -> Dict:
    try:
        conn = get_connection()
        day = since_gmt5(days=1)
        week = since_gmt5(days=7)
        mon = since_gmt5(days=30)

        def count(since: str) -> int:
            return conn.execute(
                "SELECT COUNT(*) FROM conversations WHERE company_id = ? AND created_at >= ?",
                (company_id, since),
            ).fetchone()[0]

        result = {"today": count(day), "week": count(week), "month": count(mon)}
        conn.close()
        return result
    except Exception as exc:
        print(f"[admin] _get_request_counts: {exc}")
        return {"today": 0, "week": 0, "month": 0}


def _get_top_questions(company_id: int, limit: int = 10) -> List[Dict]:
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT query, COUNT(*) as cnt
               FROM conversations WHERE company_id = ?
               GROUP BY query ORDER BY cnt DESC LIMIT ?""",
            (company_id, limit),
        ).fetchall()
        conn.close()
        return [{"query": r["query"], "count": r["cnt"]} for r in rows]
    except Exception as exc:
        print(f"[admin] _get_top_questions: {exc}")
        return []


def _get_satisfaction_rate(company_id: int) -> Optional[float]:
    try:
        conn = get_connection()
        row = conn.execute(
            """SELECT
                 SUM(CASE WHEN f.score = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS rate
               FROM feedback f
               JOIN conversations c ON f.conversation_id = c.id
               WHERE c.company_id = ?""",
            (company_id,),
        ).fetchone()
        conn.close()
        val = row[0] if row else None
        return round(float(val) * 100, 1) if val is not None else None
    except Exception as exc:
        print(f"[admin] _get_satisfaction_rate: {exc}")
        return None


def _get_document_scores(company_id: int) -> List[Dict]:
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT filename, relevance_score, usage_count
               FROM documents WHERE company_id = ?
               ORDER BY relevance_score DESC""",
            (company_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[admin] _get_document_scores: {exc}")
        return []


def _get_audit_logs(company_id: int, limit: int = 20) -> List[Dict]:
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT id, user_id, event_type, toxic_flag, payload_encrypted, created_at
               FROM audit_log WHERE company_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (company_id, limit),
        ).fetchall()
        conn.close()
        result = []
        for r in rows:
            payload = (
                decrypt(r["payload_encrypted"]) if r["payload_encrypted"] else "{}"
            )
            try:
                payload_dict = json.loads(payload)
            except Exception:
                payload_dict = {"raw": payload}
            result.append(
                {
                    "id": r["id"],
                    "user_id": r["user_id"],
                    "event_type": r["event_type"],
                    "toxic_flag": bool(r["toxic_flag"]),
                    "payload": payload_dict,
                    "created_at": utc_str_to_gmt5(r["created_at"])
                    if r["created_at"]
                    else "",
                }
            )
        return result
    except Exception as exc:
        print(f"[admin] _get_audit_logs: {exc}")
        return []


def _get_scraping_activity(company_id: int) -> List[Dict]:
    try:
        conn = get_connection()
        since = since_gmt5(hours=24)
        rows = conn.execute(
            """SELECT url, title, chunk_count, last_scraped
               FROM scraped_pages
               WHERE company_id = ? AND last_scraped >= ?
               ORDER BY last_scraped DESC""",
            (company_id, since),
        ).fetchall()
        conn.close()
        result = []
        for r in rows:
            row = dict(r)
            if row.get("last_scraped"):
                row["last_scraped"] = utc_str_to_gmt5(row["last_scraped"])
            result.append(row)
        return result
    except Exception as exc:
        print(f"[admin] _get_scraping_activity: {exc}")
        return []


# ── tab renderers ─────────────────────────────────────────────────────────────


def _tab_documents(company_id: int, user_id: int) -> None:
    st.caption("Supported formats: PDF, TXT, DOCX, MD · Max size: 50 MB")

    visibility = st.radio(
        "Visibility",
        options=["public", "worker"],
        horizontal=True,
        help="'public' → accessible by all users; 'worker' → workers and admins only",
    )

    uploaded = st.file_uploader(
        "Choose files",
        type=["pdf", "txt", "docx", "md"],
        accept_multiple_files=True,
    )

    if st.button("📥 Ingest selected files", disabled=not uploaded):
        progress = st.progress(0)
        successful_count = 0
        failed_count = 0
        for i, f in enumerate(uploaded):
            file_bytes = f.read()
            file_size = len(file_bytes)
            if file_size > 50 * 1024 * 1024:
                st.error(f"'{f.name}' exceeds 50 MB limit – skipped.")
                failed_count += 1
                pendo_track(
                    "document_ingestion_failed",
                    visitor_id=user_id,
                    account_id=company_id,
                    properties={
                        "filename": f.name,
                        "file_type": f.name.rsplit(".", 1)[-1].lower(),
                        "file_size": file_size,
                        "visibility": visibility,
                        "error_reason": "exceeds_50mb_limit",
                        "company_id": company_id,
                    },
                )
                continue
            ext = f.name.rsplit(".", 1)[-1].lower()
            with st.spinner(f"Processing '{f.name}' …"):
                ok, msg = _ingest_document(
                    file_bytes, f.name, ext, visibility, company_id, user_id
                )
            if ok:
                successful_count += 1
                st.success(msg)
                pendo_track(
                    "document_ingested",
                    visitor_id=user_id,
                    account_id=company_id,
                    properties={
                        "filename": f.name,
                        "file_type": ext,
                        "file_size": file_size,
                        "visibility": visibility,
                        "chunk_count": int(msg.split()[1]) if msg.split()[1].isdigit() else 0,
                        "company_id": company_id,
                    },
                )
            else:
                failed_count += 1
                st.error(f"'{f.name}': {msg}")
                pendo_track(
                    "document_ingestion_failed",
                    visitor_id=user_id,
                    account_id=company_id,
                    properties={
                        "filename": f.name,
                        "file_type": ext,
                        "file_size": file_size,
                        "visibility": visibility,
                        "error_reason": msg[:200],
                        "company_id": company_id,
                    },
                )
            progress.progress((i + 1) / len(uploaded))
        pendo_track(
            "bulk_document_ingestion_completed",
            visitor_id=user_id,
            account_id=company_id,
            properties={
                "total_files": len(uploaded),
                "successful_count": successful_count,
                "failed_count": failed_count,
                "visibility": visibility,
                "company_id": company_id,
            },
        )

    st.divider()
    st.subheader("📚 Indexed Documents")
    docs = _get_document_scores(company_id)
    if docs:
        st.dataframe(
            docs,
            column_config={
                "filename": "File",
                "relevance_score": st.column_config.NumberColumn(
                    "Relevance", format="%.3f"
                ),
                "usage_count": "Used",
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No documents indexed yet.")


_ANALYTICS_CSS = """
<style>
[data-testid="stMetric"] { padding: 0.2rem 0 !important; }
[data-testid="stMetricLabel"] { font-size: 0.78rem !important; }
[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
.analytics-section-title {
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6b7a8d;
    margin: 0.6rem 0 0.25rem 0;
}
.analytics-hr {
    border: none;
    border-top: 1px solid rgba(0,0,0,0.08);
    margin: 0.2rem 0;
}
</style>
"""


def _tab_analytics(company_id: int) -> None:
    st.markdown(_ANALYTICS_CSS, unsafe_allow_html=True)

    # ── Request counts ────────────────────────────────────────────
    counts = _get_request_counts(company_id)
    c1, c2, c3 = st.columns(3)
    c1.metric("Requests today", counts["today"])
    c2.metric("Requests (7d)", counts["week"])
    c3.metric("Requests (30d)", counts["month"])

    st.markdown('<hr class="analytics-hr">', unsafe_allow_html=True)

    # ── Satisfaction ──────────────────────────────────────────────
    rate = _get_satisfaction_rate(company_id)
    if rate is not None:
        st.metric("Satisfaction rate", f"{rate}%")
    else:
        st.caption("No feedback data yet.")

    st.markdown('<hr class="analytics-hr">', unsafe_allow_html=True)

    # ── Top questions ─────────────────────────────────────────────
    st.markdown(
        '<p class="analytics-section-title">Top 10 Questions</p>',
        unsafe_allow_html=True,
    )
    top_q = _get_top_questions(company_id)
    if top_q:
        rows = "".join(
            f"<div style='padding:2px 0; font-size:0.88rem;'><b>{i}.</b> {item['query']} "
            f"<span style='color:#888; font-size:0.8rem;'>— {item['count']}×</span></div>"
            for i, item in enumerate(top_q, 1)
        )
        st.markdown(rows, unsafe_allow_html=True)
    else:
        st.caption("No conversation data yet.")

    st.markdown('<hr class="analytics-hr">', unsafe_allow_html=True)

    # ── Continual learning ────────────────────────────────────────
    st.markdown(
        '<p class="analytics-section-title">Continual Learning</p>',
        unsafe_allow_html=True,
    )
    drift = drift_summary(company_id)
    col1, col2, col3 = st.columns(3)
    col1.metric("Drift status", drift["status"])
    col2.metric("Recent similarity", f"{drift['recent_sim']:.3f}")
    col3.metric("Plasticity ×", f"{drift['plasticity_mult']}")

    base_p = 0.2
    plasticity_parts = " · ".join(
        f"n={u}: {calculate_plasticity(base_p, u, drift_boost=drift['drift_detected']):.3f}"
        for u in [0, 5, 10, 20, 50]
    )
    st.caption(f"Plasticity curve — {plasticity_parts}")

    st.markdown('<hr class="analytics-hr">', unsafe_allow_html=True)

    # ── Document relevance scores ─────────────────────────────────
    st.markdown(
        '<p class="analytics-section-title">Document Relevance Scores</p>',
        unsafe_allow_html=True,
    )
    docs = _get_document_scores(company_id)
    if docs:
        rows = "".join(
            f"<div style='padding:2px 0; font-size:0.88rem;'>"
            f"<code>{d['filename']}</code> "
            f"<span style='color:#888;'>score: <b>{d['relevance_score']:.3f}</b> · used {d['usage_count']}×</span>"
            f"</div>"
            for d in docs
        )
        st.markdown(rows, unsafe_allow_html=True)
    else:
        st.caption("No documents indexed yet.")


def _tab_logs(company_id: int) -> None:
    st.subheader("🔐 Audit Logs (last 20, decrypted)")
    logs = _get_audit_logs(company_id)
    if not logs:
        st.info("No audit log entries yet.")
        return

    for entry in logs:
        toxic_badge = "🔴 TOXIC" if entry["toxic_flag"] else "🟢 OK"
        with st.expander(
            f"[{entry['created_at']}]  {entry['event_type']}  {toxic_badge}"
        ):
            st.json(entry["payload"])
            st.caption(f"user_id={entry['user_id']}  log_id={entry['id']}")


_SCRAPER_CSS = """
<style>
.scraper-section-title {
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6b7a8d;
    margin: 0.5rem 0 0.2rem 0;
}
.scraper-hr {
    border: none;
    border-top: 1px solid rgba(0,0,0,0.08);
    margin: 0.3rem 0;
}
</style>
"""


def _tab_scraper(company_id: int) -> None:
    st.markdown(_SCRAPER_CSS, unsafe_allow_html=True)

    # ── Control ───────────────────────────────────────────────────
    st.caption(f"Cron: `0 2 * * *` (07:00 GMT+5) · Now: {now_gmt5_str()}")
    col1, col2 = st.columns([1, 3])
    with col1:
        max_pages = st.number_input(
            "Max pages", min_value=10, max_value=500, value=100, step=10
        )
    with col2:
        st.markdown("<div style='margin-top:1.6rem;'></div>", unsafe_allow_html=True)
        if st.button("▶ Run scraper now"):
            user_id = st.session_state.user["id"]
            with st.spinner("Crawling https://www.pendo.io …"):
                try:
                    summary = run_update(company_id=company_id, max_pages=max_pages)
                    pendo_track(
                        "scraper_run_completed",
                        visitor_id=user_id,
                        account_id=company_id,
                        properties={
                            "pages_added": summary["added"],
                            "pages_updated": summary["updated"],
                            "pages_removed": summary["removed"],
                            "pages_unchanged": summary["unchanged"],
                            "errors": summary["errors"],
                            "max_pages": max_pages,
                            "company_id": company_id,
                        },
                    )
                    st.success(
                        f"Done — added: {summary['added']} · "
                        f"updated: {summary['updated']} · "
                        f"removed: {summary['removed']} · "
                        f"unchanged: {summary['unchanged']} · "
                        f"errors: {summary['errors']}"
                    )
                except Exception as exc:
                    pendo_track(
                        "scraper_run_failed",
                        visitor_id=user_id,
                        account_id=company_id,
                        properties={
                            "error_message": str(exc)[:200],
                            "max_pages": max_pages,
                            "company_id": company_id,
                        },
                    )
                    st.error(f"Scraper error: {exc}")

    st.markdown('<hr class="scraper-hr">', unsafe_allow_html=True)

    # ── Recent activity ───────────────────────────────────────────
    st.markdown(
        '<p class="scraper-section-title">Scraped Pages — last 24 h</p>',
        unsafe_allow_html=True,
    )
    activity = _get_scraping_activity(company_id)
    if activity:
        st.dataframe(
            activity,
            column_config={
                "url": "URL",
                "title": "Title",
                "chunk_count": "Chunks",
                "last_scraped": "Last scraped",
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No scraping activity in the last 24 hours.")

    st.markdown('<hr class="scraper-hr">', unsafe_allow_html=True)

    # ── Totals ────────────────────────────────────────────────────
    st.markdown(
        '<p class="scraper-section-title">Total Scraped Pages</p>',
        unsafe_allow_html=True,
    )
    try:
        conn = get_connection()
        total = conn.execute(
            "SELECT COUNT(*) FROM scraped_pages WHERE company_id = ?", (company_id,)
        ).fetchone()[0]
        total_chunks = conn.execute(
            "SELECT COALESCE(SUM(chunk_count),0) FROM scraped_pages WHERE company_id = ?",
            (company_id,),
        ).fetchone()[0]
        conn.close()
        c1, c2 = st.columns(2)
        c1.metric("Pages indexed", total)
        c2.metric("Total chunks", total_chunks)
    except Exception as exc:
        st.error(f"Could not fetch stats: {exc}")


# ── page render ───────────────────────────────────────────────────────────────


def render() -> None:
    if not _require_admin():
        return

    user: Dict = st.session_state.user
    company_id: int = st.session_state.get("company_id", 1)

    from utils.sidebar import render_admin_sidebar

    render_admin_sidebar(user, on_admin_page=True)

    section = st.session_state.get("admin_section", "documents")

    if section == "documents":
        st.title("Upload Documents")
        _tab_documents(company_id, user["id"])
    elif section == "analytics":
        st.title("Usage Analytics")
        _tab_analytics(company_id)
    elif section == "logs":
        st.title("Logs")
        _tab_logs(company_id)
    elif section == "scraper":
        st.title("Web Scraper Control")
        _tab_scraper(company_id)


render()
