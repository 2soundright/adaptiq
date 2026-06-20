"""
pipeline/embeddings.py
----------------------
Step 4 of the RAG pipeline.
Primary:  BAAI/bge-m3 via HuggingFace Inference API (httpx, sync).
Fallback: sentence-transformers/all-MiniLM-L6-v2 loaded locally.
"""

import os
import time
from typing import List, Optional

import httpx
import numpy as np

_HF_TOKEN          = os.getenv("HF_TOKEN", "")
_HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "BAAI/bge-m3")
_HF_API_BASE       = "https://router.huggingface.co/models"
_TIMEOUT           = 60.0   # seconds
_MAX_RETRIES       = 3
_RETRY_DELAY       = 2.0    # seconds

# Lazy-loaded local fallback model
_local_model = None


def _get_local_model():
    """Lazy-load the local sentence-transformers fallback model."""
    global _local_model
    if _local_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _local_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            print("[embeddings] Loaded local fallback model: all-MiniLM-L6-v2")
        except Exception as exc:
            raise RuntimeError(f"Failed to load local embedding model: {exc}") from exc
    return _local_model


def _embed_hf_api(texts: List[str]) -> Optional[List[List[float]]]:
    """
    Call HuggingFace Inference API for BAAI/bge-m3 embeddings.
    Returns list of embedding vectors, or None on failure.
    """
    if not _HF_TOKEN:
        return None

    url = f"{_HF_API_BASE}/{_HF_EMBEDDING_MODEL}"
    headers = {
        "Authorization": f"Bearer {_HF_TOKEN}",
        "Content-Type":  "application/json",
    }
    payload = {
        "inputs": texts,
        "options": {"wait_for_model": True},
    }

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(url, headers=headers, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                # HF API returns list of lists or nested structure
                if isinstance(data, list) and len(data) > 0:
                    # Some models return [[emb]] for single input
                    if isinstance(data[0], list) and isinstance(data[0][0], float):
                        return data
                    # Nested: [[[float,...]]]
                    if isinstance(data[0], list) and isinstance(data[0][0], list):
                        return [item[0] for item in data]
                return None

            if resp.status_code == 503:
                # Model loading – wait and retry
                wait = float(resp.json().get("estimated_time", _RETRY_DELAY))
                print(f"[embeddings] HF model loading, waiting {wait:.1f}s …")
                time.sleep(min(wait, 30.0))
                continue

            print(f"[embeddings] HF API returned {resp.status_code}: {resp.text[:200]}")
            return None

        except httpx.TimeoutException:
            print(f"[embeddings] HF API timeout on attempt {attempt}/{_MAX_RETRIES}")
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)
        except Exception as exc:
            print(f"[embeddings] HF API error on attempt {attempt}/{_MAX_RETRIES}: {exc}")
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)

    return None


def _embed_local(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using local sentence-transformers model."""
    try:
        model = _get_local_model()
        vectors = model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()
    except Exception as exc:
        raise RuntimeError(f"Local embedding failed: {exc}") from exc


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of texts.
    Tries HF API first, falls back to local model.

    Returns:
        List of float vectors (one per input text).

    Raises:
        RuntimeError if both primary and fallback fail.
    """
    if not texts:
        return []

    # Normalise inputs
    clean = [t.strip() if t else " " for t in texts]

    # Try HF API
    result = _embed_hf_api(clean)
    if result and len(result) == len(clean):
        return result

    print("[embeddings] Falling back to local MiniLM model.")
    return _embed_local(clean)


def embed_single(text: str) -> List[float]:
    """Convenience wrapper to embed a single string."""
    vectors = embed_texts([text])
    return vectors[0] if vectors else []


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    try:
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        denom = (np.linalg.norm(va) * np.linalg.norm(vb))
        if denom == 0.0:
            return 0.0
        return float(np.dot(va, vb) / denom)
    except Exception as exc:
        print(f"[embeddings] cosine_similarity error: {exc}")
        return 0.0
