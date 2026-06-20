"""
pipeline/feedback.py
--------------------
Step 8 of the RAG pipeline.
Accepts +1 / -1 ratings, analyses them with llama-3.1-8b-instant,
and updates the relevance_score of contributing chunks via EWC plasticity.
"""

import json
import os
from typing import Dict, List, Optional

from groq import Groq

from utils.db_init import get_connection
from utils.db_lock import db_lock
from continual_learning.ewc import calculate_plasticity

_GROQ_FEEDBACK_MODEL = os.getenv("GROQ_FEEDBACK_MODEL", "llama-3.1-8b-instant")

_ANALYSIS_PROMPT = """You are a feedback quality analyser.
Given a user's query, the assistant's response, and a rating (+1 = helpful, -1 = not helpful),
briefly explain in 1-2 sentences why the user likely gave this rating.
Return ONLY a JSON object: {"analysis": "your explanation"}"""


def _analyse_feedback(query: str, response: str, score: int) -> str:
    """Use LLaMA to generate a short analysis of the feedback."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return "Analysis unavailable (no API key)."

    try:
        client = Groq(api_key=api_key)
        user_content = (
            f"Query: {query}\n"
            f"Response: {response[:500]}\n"
            f"Rating: {'👍 +1 (helpful)' if score == 1 else '👎 -1 (not helpful)'}"
        )
        resp = client.chat.completions.create(
            model=_GROQ_FEEDBACK_MODEL,
            messages=[
                {"role": "system", "content": _ANALYSIS_PROMPT},
                {"role": "user",   "content": user_content},
            ],
            temperature=0.3,
            max_tokens=128,
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
        return str(data.get("analysis", raw))
    except Exception as exc:
        print(f"[feedback] LLM analysis failed: {exc}")
        return f"Feedback: {'positive' if score == 1 else 'negative'}."


def _update_chunk_scores(
    chunk_ids: List[str],
    company_id: int,
    role: str,
    score: int,
) -> None:
    """
    Update relevance_score for each chunk that contributed to the answer.
    new_score = old_score * (1 - plasticity) + feedback_value * plasticity
    """
    from pipeline.retriever import update_chunk_relevance
    from pipeline.retriever import get_or_create_collection

    feedback_value = 1.0 if score == 1 else 0.0

    try:
        collection = get_or_create_collection(company_id, role)
        if not chunk_ids:
            return

        existing = collection.get(ids=chunk_ids, include=["metadatas"])
        for doc_id, meta in zip(existing["ids"], existing["metadatas"]):
            meta = meta or {}
            old_score   = float(meta.get("relevance_score", 1.0))
            usage_count = int(meta.get("usage_count",    0))
            plasticity  = calculate_plasticity(
                base_plasticity=0.2,
                usage_count=usage_count,
            )
            new_score = old_score * (1.0 - plasticity) + feedback_value * plasticity
            new_score = max(0.0, min(2.0, new_score))   # clamp to [0, 2]
            update_chunk_relevance(doc_id, company_id, role, new_score)
    except Exception as exc:
        print(f"[feedback] Chunk score update failed: {exc}")


def save_feedback(
    conversation_id: int,
    user_id: int,
    score: int,
    chunk_ids: Optional[List[str]] = None,
    company_id: Optional[int] = None,
    role: str = "user",
    star_rating: Optional[int] = None,
    comment: Optional[str] = None,
) -> bool:
    """
    Persist user feedback and trigger relevance updates.

    Args:
        conversation_id: FK to conversations table.
        user_id:         FK to users table.
        score:           +1 or -1 (derived from star_rating if provided).
        chunk_ids:       ChromaDB chunk IDs used in the answer.
        company_id:      For collection selection.
        role:            User role.
        star_rating:     1–5 star rating given by user.
        comment:         Optional text comment from user.

    Returns:
        True on success, False on failure.
    """
    if score not in (1, -1):
        print(f"[feedback] Invalid score {score}; must be +1 or -1.")
        return False

    # Fetch conversation details for analysis
    analysis = ""
    try:
        conn = get_connection()
        conv = conn.execute(
            "SELECT query, response FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        conn.close()
        if conv:
            analysis = _analyse_feedback(conv["query"], conv["response"], score)
    except Exception as exc:
        print(f"[feedback] Failed to fetch conversation: {exc}")

    # Persist feedback row
    try:
        with db_lock():
            conn = get_connection()
            conn.execute(
                "INSERT INTO feedback (conversation_id, user_id, score, analysis, star_rating, comment) "
                "VALUES (?,?,?,?,?,?)",
                (conversation_id, user_id, score, analysis, star_rating, comment),
            )
            conn.commit()
            conn.close()
    except Exception as exc:
        print(f"[feedback] DB write failed: {exc}")
        return False

    # Update chunk relevance scores
    if chunk_ids and company_id is not None:
        _update_chunk_scores(chunk_ids, company_id, role, score)

    return True
