"""
pipeline/retriever.py
---------------------
Step 5 of the RAG pipeline.
Queries ChromaDB for the top-10 most relevant chunks.
Collection is selected based on the user's role:
  user   → company_{id}_public
  worker → company_{id}_worker
  admin  → company_{id}_public
All writes are protected by db_lock().
"""

import os
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings

from utils.db_lock import db_lock

_DEFAULT_CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "chroma_db")
_CHROMA_PATH = os.getenv("CHROMA_PATH", _DEFAULT_CHROMA_PATH)
_TOP_K       = 10

# Singleton ChromaDB client
_chroma_client: Optional[chromadb.PersistentClient] = None


def _get_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        try:
            os.makedirs(_CHROMA_PATH, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(
                path=_CHROMA_PATH,
                settings=Settings(anonymized_telemetry=False),
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to init ChromaDB client: {exc}") from exc
    return _chroma_client


def _collection_name(company_id: int, role: str) -> str:
    """Map role → ChromaDB collection name."""
    if role == "worker":
        return f"company_{company_id}_worker"
    return f"company_{company_id}_public"


def get_or_create_collection(
    company_id: int,
    role: str = "user",
) -> Any:
    """Return (or create) the ChromaDB collection for a company + role."""
    name = _collection_name(company_id, role)
    try:
        client = _get_client()
        with db_lock():
            collection = client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return collection
    except Exception as exc:
        raise RuntimeError(
            f"Failed to get/create ChromaDB collection '{name}': {exc}"
        ) from exc


def retrieve(
    query_embedding: List[float],
    company_id: int,
    role: str = "user",
    top_k: int = _TOP_K,
) -> List[Dict]:
    """
    Query ChromaDB and return up to *top_k* result chunks.

    Returns:
        List of dicts with keys: id, text, metadata, distance
    """
    if not query_embedding:
        return []
    try:
        collection = get_or_create_collection(company_id, role)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        print(f"[retriever] ChromaDB query failed: {exc}")
        return []

    chunks: List[Dict] = []
    try:
        ids       = results.get("ids",       [[]])[0]
        docs      = results.get("documents", [[]])[0]
        metas     = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, (doc_id, text, meta, dist) in enumerate(
            zip(ids, docs, metas, distances)
        ):
            chunks.append(
                {
                    "id":       doc_id,
                    "text":     text or "",
                    "metadata": meta  or {},
                    "distance": float(dist),
                    "score":    1.0 - float(dist),   # cosine similarity approx
                }
            )
    except Exception as exc:
        print(f"[retriever] Result parsing error: {exc}")

    return chunks


def add_chunks(
    company_id: int,
    role: str,
    ids: List[str],
    texts: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict],
) -> None:
    """
    Insert or update chunks in ChromaDB.
    Protected by db_lock().
    """
    if not ids:
        return
    try:
        collection = get_or_create_collection(company_id, role)
        with db_lock():
            collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
    except Exception as exc:
        raise RuntimeError(f"add_chunks failed: {exc}") from exc


def delete_chunks_by_source(
    company_id: int,
    role: str,
    source_url: str,
) -> int:
    """
    Delete all chunks whose metadata.website_url equals *source_url*.
    Returns the number of deleted chunks.
    """
    try:
        collection = get_or_create_collection(company_id, role)
        results = collection.get(
            where={"website_url": source_url},
            include=["metadatas"],
        )
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            with db_lock():
                collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)
    except Exception as exc:
        print(f"[retriever] delete_chunks_by_source error: {exc}")
        return 0


def update_chunk_relevance(chunk_id: str, company_id: int, role: str, new_score: float) -> None:
    """Update the relevance_score metadata field for a single chunk."""
    try:
        collection = get_or_create_collection(company_id, role)
        existing = collection.get(ids=[chunk_id], include=["metadatas", "documents", "embeddings"])
        if not existing["ids"]:
            return
        meta = existing["metadatas"][0] or {}
        meta["relevance_score"] = round(new_score, 6)
        with db_lock():
            collection.update(
                ids=[chunk_id],
                metadatas=[meta],
            )
    except Exception as exc:
        print(f"[retriever] update_chunk_relevance error: {exc}")
