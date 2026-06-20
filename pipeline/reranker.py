"""
pipeline/reranker.py
--------------------
Step 6 of the RAG pipeline.
Primary:  BAAI/bge-reranker-large via HuggingFace Inference API.
Fallback: sort by ChromaDB cosine similarity score and keep top-3.
"""

import os
import time
from typing import Dict, List, Optional

import httpx

_HF_TOKEN         = os.getenv("HF_TOKEN", "")
_HF_RERANKER_MODEL = os.getenv("HF_RERANKER_MODEL", "BAAI/bge-reranker-large")
_HF_API_BASE      = "https://router.huggingface.co/models"
_TIMEOUT          = 60.0
_MAX_RETRIES      = 3
_TOP_N            = 3


def _call_reranker_api(
    query: str,
    documents: List[str],
) -> Optional[List[float]]:
    """
    Call the HF cross-encoder reranker API.
    Returns a list of relevance scores (one per document), or None on failure.
    """
    if not _HF_TOKEN or not documents:
        return None

    url = f"{_HF_API_BASE}/{_HF_RERANKER_MODEL}"
    headers = {
        "Authorization": f"Bearer {_HF_TOKEN}",
        "Content-Type":  "application/json",
    }
    # bge-reranker-large expects pairs via text-ranking / text-classification
    payload = {
        "inputs": {
            "source_sentence": query,
            "sentences": documents,
        },
        "options": {"wait_for_model": True},
    }

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(url, headers=headers, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                # Response may be:
                # [score, score, ...] (list of floats)
                # [{"score": float}, ...] (list of dicts)
                if isinstance(data, list) and len(data) == len(documents):
                    if isinstance(data[0], (int, float)):
                        return [float(s) for s in data]
                    if isinstance(data[0], dict):
                        return [float(d.get("score", 0.0)) for d in data]
                return None

            if resp.status_code == 503:
                wait = float(resp.json().get("estimated_time", 3.0))
                print(f"[reranker] HF model loading, waiting {wait:.1f}s …")
                time.sleep(min(wait, 30.0))
                continue

            print(f"[reranker] HF API returned {resp.status_code}: {resp.text[:200]}")
            return None

        except httpx.TimeoutException:
            print(f"[reranker] HF timeout attempt {attempt}/{_MAX_RETRIES}")
            if attempt < _MAX_RETRIES:
                time.sleep(2.0)
        except Exception as exc:
            print(f"[reranker] HF error attempt {attempt}/{_MAX_RETRIES}: {exc}")
            if attempt < _MAX_RETRIES:
                time.sleep(2.0)

    return None


def rerank(
    query: str,
    chunks: List[Dict],
    top_n: int = _TOP_N,
) -> List[Dict]:
    """
    Rerank *chunks* against *query* and return the top *top_n*.

    Each chunk dict must have at least 'text' and 'score' keys.

    Returns:
        Sorted list of chunk dicts (best first), length <= top_n.
    """
    if not chunks:
        return []

    if len(chunks) <= top_n:
        return sorted(chunks, key=lambda c: c.get("score", 0.0), reverse=True)

    texts = [c.get("text", "") for c in chunks]

    scores = _call_reranker_api(query, texts)

    if scores and len(scores) == len(chunks):
        # Attach reranker score and sort
        for chunk, s in zip(chunks, scores):
            chunk["rerank_score"] = float(s)
        ranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
    else:
        # Fallback: use original similarity score from retriever
        print("[reranker] HF reranker unavailable – using similarity fallback.")
        ranked = sorted(chunks, key=lambda c: c.get("score", 0.0), reverse=True)

    return ranked[:top_n]
