# RAG Pipeline Architecture

## How AdaptIQ Answers Questions

Every user query passes through an 8-step Retrieval-Augmented Generation (RAG) pipeline before an answer is generated:

| Step | Name | What It Does |
|------|------|------|
| 1 | **Safety Check** | Detects toxic content, harmful requests, and prompt injection attempts using an LLM safety classifier. Blocked queries are logged to the audit trail. |
| 2 | **Language Detection** | Identifies whether the query is in English, Russian, or Kazakh. The response is generated in the same language. |
| 3 | **Query Transformation** | Expands and rewrites the query for better retrieval results. Also strips known injection patterns as a second safety layer. |
| 4 | **Embedding** | Converts the transformed query into a numerical vector using BAAI/bge-m3 (with a local MiniLM fallback). |
| 5 | **Retrieval** | Queries the ChromaDB vector database for the top 10 most semantically similar document chunks, scoped by the user's role and company. |
| 6 | **Reranking** | Uses a cross-encoder model (BAAI/bge-reranker-large) to re-score and select the top 3 most relevant chunks. |
| 7 | **Generation** | Streams the AI response token-by-token using an LLM via Groq, grounding the answer in the retrieved document context. |
| 8 | **Feedback** | Collects user ratings (1-5 stars + optional comment) and uses them to adjust document relevance scores through continual learning. |

This pipeline ensures answers are grounded in company knowledge, safe from abuse, and continuously improving based on user feedback.
