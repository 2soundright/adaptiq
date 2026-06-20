"""
continual_learning/replay_buffer.py
------------------------------------
Stores the last 500 Q&A pairs (with embeddings) in SQLite.
On each model-update cycle, samples 50 entries to replay.
All writes are protected by db_lock().
"""

import json
import random
from typing import Dict, List, Optional, Tuple

from utils.db_init import get_connection
from utils.db_lock import db_lock

_MAX_BUFFER_SIZE = 500
_SAMPLE_SIZE     = 50


def add_entry(
    company_id: int,
    query: str,
    response: str,
    embedding: List[float],
    quality_score: float = 0.5,
) -> None:
    """
    Insert a new Q&A entry into the replay buffer.
    If the buffer exceeds MAX_BUFFER_SIZE, the oldest entries are pruned.

    Args:
        company_id:    Company this entry belongs to.
        query:         User query text.
        response:      Assistant response text.
        embedding:     Query embedding vector.
        quality_score: Initial quality score (0.0–1.0).
    """
    try:
        embedding_json = json.dumps(embedding)
        with db_lock():
            conn = get_connection()
            conn.execute(
                """INSERT INTO replay_buffer
                   (company_id, query, response, embedding_json, quality_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (company_id, query, response, embedding_json, quality_score),
            )

            # Prune oldest entries if buffer is over capacity
            conn.execute(
                """DELETE FROM replay_buffer
                   WHERE company_id = ?
                     AND id NOT IN (
                         SELECT id FROM replay_buffer
                         WHERE company_id = ?
                         ORDER BY created_at DESC
                         LIMIT ?
                     )""",
                (company_id, company_id, _MAX_BUFFER_SIZE),
            )
            conn.commit()
            conn.close()
    except Exception as exc:
        print(f"[replay_buffer] add_entry failed: {exc}")


def sample_entries(
    company_id: int,
    n: int = _SAMPLE_SIZE,
) -> List[Dict]:
    """
    Return up to *n* randomly sampled entries from the buffer for a company.

    Returns:
        List of dicts with keys: id, query, response, embedding, quality_score.
    """
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT id, query, response, embedding_json, quality_score
               FROM replay_buffer
               WHERE company_id = ?
               ORDER BY RANDOM()
               LIMIT ?""",
            (company_id, n),
        ).fetchall()
        conn.close()

        entries: List[Dict] = []
        for row in rows:
            try:
                emb = json.loads(row["embedding_json"])
            except (json.JSONDecodeError, TypeError):
                emb = []
            entries.append(
                {
                    "id":            row["id"],
                    "query":         row["query"],
                    "response":      row["response"],
                    "embedding":     emb,
                    "quality_score": row["quality_score"],
                }
            )
        return entries
    except Exception as exc:
        print(f"[replay_buffer] sample_entries failed: {exc}")
        return []


def get_recent_embeddings(
    company_id: int,
    limit: int = 100,
) -> List[List[float]]:
    """
    Return the embeddings of the most recent *limit* entries.
    Used by the drift detector.
    """
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT embedding_json FROM replay_buffer
               WHERE company_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (company_id, limit),
        ).fetchall()
        conn.close()

        embeddings: List[List[float]] = []
        for row in rows:
            try:
                emb = json.loads(row["embedding_json"])
                if emb:
                    embeddings.append(emb)
            except (json.JSONDecodeError, TypeError):
                pass
        return embeddings
    except Exception as exc:
        print(f"[replay_buffer] get_recent_embeddings failed: {exc}")
        return []


def buffer_size(company_id: int) -> int:
    """Return the current number of entries in the buffer for a company."""
    try:
        conn = get_connection()
        count = conn.execute(
            "SELECT COUNT(*) FROM replay_buffer WHERE company_id = ?",
            (company_id,),
        ).fetchone()[0]
        conn.close()
        return int(count)
    except Exception as exc:
        print(f"[replay_buffer] buffer_size failed: {exc}")
        return 0
