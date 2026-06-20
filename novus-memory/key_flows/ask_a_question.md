# Ask a Question (Core RAG Pipeline)

The primary value flow — users ask questions in natural language and receive AI-generated answers grounded in the company's knowledge base documents and scraped web content. The answer includes source citations and a feedback mechanism.

**Persona:** All Users

1. User sees the welcome screen with 'Ask me anything — I'm here to help'
2. User types a question in the chat input and presses enter
3. System runs safety check to detect toxic content or prompt injection attempts
4. System detects the query language (English, Russian, or Kazakh)
5. System transforms/expands the query for better retrieval, stripping any injection patterns
6. System generates an embedding vector for the transformed query
7. System retrieves the top 10 most relevant document chunks from the vector database
8. System reranks results using a cross-encoder model and selects the top 3 chunks
9. System streams the AI-generated response token by token in the chat interface
10. Source citations appear below the response with links and expandable excerpts
11. User can rate the response (1-5 stars) and leave an optional comment
12. Feedback updates document relevance scores via the continual learning system
