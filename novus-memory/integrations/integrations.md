# Integrations

Third-party integrations connected to AdaptIQ.

| NAME | DESCRIPTION |
|------|-------------|
| [Groq](groq.md) | Powers the core AI capabilities including response generation (LLM streaming), content safety classification, query transformation/expansion, and feedback analysis. Uses multiple models: a large model for generation, a smaller model for query transformation and feedback analysis, and a safety-specific model for content moderation. |
| [HuggingFace Inference API](huggingface.md) | Provides two key AI services: (1) text embeddings via BAAI/bge-m3 for converting queries and documents into vector representations for semantic search, and (2) cross-encoder reranking via BAAI/bge-reranker-large for refining retrieval results. Both services have local fallback models if the API is unavailable. |
| [ChromaDB](chromadb.md) | Serves as the vector database for storing and searching document embeddings. Maintains separate collections per company and role (public vs worker) for content isolation. Supports cosine similarity search for semantic retrieval of relevant document chunks. |
