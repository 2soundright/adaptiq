# HuggingFace Inference API

Provides two key AI services: (1) text embeddings via BAAI/bge-m3 for converting queries and documents into vector representations for semantic search, and (2) cross-encoder reranking via BAAI/bge-reranker-large for refining retrieval results. Both services have local fallback models if the API is unavailable.
