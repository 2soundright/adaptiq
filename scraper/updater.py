"""
scraper/updater.py
------------------
Incremental updater for the scraped content knowledge base.

Logic:
  - Fetch all /en, /ru, /kz pages via crawler.
  - Compare MD5 hashes against the scraped_pages table.
  - Insert / re-chunk new or changed pages into ChromaDB.
  - Remove deleted pages from ChromaDB and the DB.
  - Cron: 0 2 * * *  (runs at 02:00 every night)
"""

import os
import time
import uuid
from typing import Dict, List, Optional

from scraper.crawler import crawl
from pipeline.embeddings import embed_texts
from pipeline.retriever import add_chunks, delete_chunks_by_source
from utils.db_init import get_connection
from utils.db_lock import db_lock

_CHUNK_SIZE    = 512    # characters per chunk (approximate)
_CHUNK_OVERLAP = 64     # character overlap between chunks
_DEFAULT_COMPANY_ID  = int(os.getenv("DEFAULT_COMPANY_ID", "1"))
_DEFAULT_VISIBILITY  = "public"


# ── text chunking ─────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping character-level chunks."""
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_stored_hashes(company_id: int) -> Dict[str, str]:
    """Return {url: content_hash} for all scraped pages of a company."""
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT url, content_hash FROM scraped_pages WHERE company_id = ?",
            (company_id,),
        ).fetchall()
        conn.close()
        return {row["url"]: row["content_hash"] for row in rows}
    except Exception as exc:
        print(f"[updater] _get_stored_hashes failed: {exc}")
        return {}


def _upsert_scraped_page(
    company_id: int,
    url: str,
    title: str,
    content_hash: str,
    chunk_count: int,
) -> None:
    """Insert or update a scraped_pages record."""
    try:
        with db_lock():
            conn = get_connection()
            conn.execute(
                """INSERT INTO scraped_pages (company_id, url, title, content_hash, chunk_count, last_scraped)
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(company_id, url)
                   DO UPDATE SET
                       title        = excluded.title,
                       content_hash = excluded.content_hash,
                       chunk_count  = excluded.chunk_count,
                       last_scraped = CURRENT_TIMESTAMP""",
                (company_id, url, title, content_hash, chunk_count),
            )
            conn.commit()
            conn.close()
    except Exception as exc:
        print(f"[updater] _upsert_scraped_page failed for {url}: {exc}")


def _delete_scraped_page(company_id: int, url: str) -> None:
    """Remove a scraped_pages record."""
    try:
        with db_lock():
            conn = get_connection()
            conn.execute(
                "DELETE FROM scraped_pages WHERE company_id = ? AND url = ?",
                (company_id, url),
            )
            conn.commit()
            conn.close()
    except Exception as exc:
        print(f"[updater] _delete_scraped_page failed for {url}: {exc}")


# ── chunk indexing ────────────────────────────────────────────────────────────

def _index_page(
    company_id: int,
    page: Dict,
    visibility: str = _DEFAULT_VISIBILITY,
) -> int:
    """
    Chunk, embed, and upsert a single page into ChromaDB.
    Returns the number of chunks indexed.
    """
    url   = page["url"]
    title = page.get("title", url)
    text  = page.get("text", "")

    if not text.strip():
        return 0

    chunks = _chunk_text(text)
    if not chunks:
        return 0

    try:
        embeddings = embed_texts(chunks)
    except Exception as exc:
        print(f"[updater] embed_texts failed for {url}: {exc}")
        return 0

    if len(embeddings) != len(chunks):
        print(f"[updater] Embedding count mismatch for {url}: {len(embeddings)} vs {len(chunks)}")
        return 0

    ids      = [str(uuid.uuid5(uuid.NAMESPACE_URL, f"{url}#chunk{i}")) for i in range(len(chunks))]
    metadatas = [
        {
            "source_file":     "",
            "page_num":        0,
            "company_id":      company_id,
            "website_url":     url,
            "title":           title,
            "relevance_score": 1.0,
            "visibility":      visibility,
            "usage_count":     0,
        }
        for i in range(len(chunks))
    ]

    role = "user"   # public pages go to the public collection
    add_chunks(company_id, role, ids, chunks, embeddings, metadatas)
    return len(chunks)


# ── main update routine ───────────────────────────────────────────────────────

def run_update(
    company_id: int = _DEFAULT_COMPANY_ID,
    max_pages: int = 300,
) -> Dict:
    """
    Run a full incremental update:
      1. Crawl the target website
      2. Compare hashes
      3. Index new/changed pages
      4. Remove deleted pages

    Returns:
        Summary dict: {added, updated, removed, unchanged, errors}
    """
    summary = {"added": 0, "updated": 0, "removed": 0, "unchanged": 0, "errors": 0}

    print(f"[updater] Starting scrape for company {company_id} …")
    t0 = time.time()

    # Step 1 – crawl
    try:
        pages = crawl(max_pages=max_pages)
    except Exception as exc:
        print(f"[updater] Crawl failed: {exc}")
        summary["errors"] += 1
        return summary

    crawled_urls = {p["url"] for p in pages}
    stored_hashes = _get_stored_hashes(company_id)
    stored_urls   = set(stored_hashes.keys())

    # Step 2 – remove deleted pages
    deleted_urls = stored_urls - crawled_urls
    for url in deleted_urls:
        try:
            removed = delete_chunks_by_source(company_id, "user", url)
            _delete_scraped_page(company_id, url)
            summary["removed"] += 1
            print(f"[updater] Removed {removed} chunks for deleted page: {url}")
        except Exception as exc:
            print(f"[updater] Error removing {url}: {exc}")
            summary["errors"] += 1

    # Step 3 – index new / changed pages
    for page in pages:
        url   = page["url"]
        hash_ = page["content_hash"]

        if url in stored_hashes and stored_hashes[url] == hash_:
            summary["unchanged"] += 1
            continue

        action = "updated" if url in stored_hashes else "added"

        # Re-index: delete old chunks first if updating
        if action == "updated":
            try:
                delete_chunks_by_source(company_id, "user", url)
            except Exception as exc:
                print(f"[updater] Could not delete old chunks for {url}: {exc}")

        try:
            n_chunks = _index_page(company_id, page)
            _upsert_scraped_page(company_id, url, page.get("title", url), hash_, n_chunks)
            summary[action] += 1
            print(f"[updater] {action.capitalize()} {url} ({n_chunks} chunks)")
        except Exception as exc:
            print(f"[updater] Index error for {url}: {exc}")
            summary["errors"] += 1

    elapsed = time.time() - t0
    print(
        f"[updater] Done in {elapsed:.1f}s – "
        f"added={summary['added']} updated={summary['updated']} "
        f"removed={summary['removed']} unchanged={summary['unchanged']} "
        f"errors={summary['errors']}"
    )
    return summary


# ── cron entrypoint ───────────────────────────────────────────────────────────

def run_cron_job() -> None:
    """Entrypoint called by the cron scheduler (0 2 * * *)."""
    print("[updater] Cron job started.")
    try:
        run_update()
    except Exception as exc:
        print(f"[updater] Cron job error: {exc}")
    print("[updater] Cron job finished.")
