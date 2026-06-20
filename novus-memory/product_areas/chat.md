# Chat

The core product experience — a conversational AI interface where users ask questions and receive intelligent, document-grounded answers. Behind the scenes, each query passes through an 8-step RAG pipeline: safety check, language detection, query transformation, embedding, retrieval, reranking, streaming response generation, and feedback collection. Answers include source citations with links and text excerpts, and users can rate responses with a 1-5 star system plus optional comments.

## Key Features

- Natural language Q&A with streaming AI-generated responses
- Source citations with clickable links and expandable text excerpts
- Safety filtering that blocks toxic, harmful, or prompt-injection queries
- Automatic language detection supporting English, Russian, and Kazakh
- Query expansion and transformation for better retrieval results
- Conversation history context for follow-up questions
- Star rating feedback system (1-5 stars) with optional comments
- Role-based content access — workers see internal docs, regular users see public content only
- Welcome screen for first-time or new-session users
