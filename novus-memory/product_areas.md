# Product Areas

## Authentication
Handles user login, registration, and session management. Users authenticate with email and password, and are associated with a specific company. The system supports three roles (user, worker, admin) which determine access to different features and content collections. Passwords are securely hashed with bcrypt. On first launch, a default admin and regular user account are seeded automatically.

**Key Features:**
- Email and password login with bcrypt-hashed credential verification
- Self-service registration with role selection (user or worker)
- Role-based access control: user, worker, and admin roles
- Company-scoped authentication — users belong to a specific company
- Automatic session management with login persistence and logout
- Default admin and user accounts seeded on first database initialization

## Chat
The core product experience — a conversational AI interface where users ask questions and receive intelligent, document-grounded answers. Behind the scenes, each query passes through an 8-step RAG pipeline: safety check, language detection, query transformation, embedding, retrieval, reranking, streaming response generation, and feedback collection. Answers include source citations with links and text excerpts, and users can rate responses with a 1-5 star system plus optional comments.

**Key Features:**
- Natural language Q&A with streaming AI-generated responses
- Source citations with clickable links and expandable text excerpts
- Safety filtering that blocks toxic, harmful, or prompt-injection queries
- Automatic language detection supporting English, Russian, and Kazakh
- Query expansion and transformation for better retrieval results
- Conversation history context for follow-up questions
- Star rating feedback system (1-5 stars) with optional comments
- Role-based content access — workers see internal docs, regular users see public content only
- Welcome screen for first-time or new-session users

## Document Management
An admin-only area for uploading and managing knowledge base documents. Admins can upload PDF, TXT, DOCX, and Markdown files (up to 50 MB each) which are automatically parsed, chunked into segments, embedded using AI models, and indexed into the vector database. Documents can be set as 'public' (visible to all users) or 'worker' (visible only to workers and admins). The system tracks document relevance scores and usage counts that evolve over time based on user feedback.

**Key Features:**
- Multi-format document upload: PDF, TXT, DOCX, and Markdown
- 50 MB file size limit with batch upload support
- Automatic text extraction, chunking, embedding, and vector indexing
- Visibility control: public (all users) or worker (workers and admins only)
- Document relevance scoring that adapts based on user feedback
- Usage tracking showing how often each document's content is retrieved
- Indexed documents table showing files, relevance scores, and usage counts

## Analytics
An admin-only dashboard providing usage statistics, satisfaction metrics, continual learning health indicators, and document performance scores. Helps administrators understand how the AI assistant is being used, whether users are satisfied with responses, and whether the knowledge base is drifting or stable.

**Key Features:**
- Request volume metrics: today, 7-day, and 30-day conversation counts
- User satisfaction rate calculated from feedback scores
- Top 10 most frequently asked questions with occurrence counts
- Continual learning dashboard: drift status, similarity metrics, and plasticity curve
- Document relevance scores showing which documents perform best
- Drift detection status indicating whether query patterns are shifting

## Audit Logs
An admin-only security monitoring area that displays encrypted audit log entries. All sensitive events — particularly safety blocks on toxic or malicious queries — are logged with encrypted payloads using Fernet symmetric encryption. Admins can view decrypted log entries to monitor system security, review blocked queries, and identify problematic usage patterns.

**Key Features:**
- Last 20 audit log entries displayed with decrypted payloads
- Toxic/safe status badges for each log entry (red TOXIC vs green OK)
- Fernet-encrypted payload storage for security compliance
- Event type classification (e.g., safety_block events)
- User ID and timestamp tracking for each audit event
- Expandable detail view with full JSON payload for each entry

## Web Scraper
An admin-only tool for automatically crawling and indexing a company's website content into the knowledge base. The scraper performs breadth-first crawling of the configured company website, extracts meaningful text from pages, chunks and embeds the content, and stores it in the vector database. It supports incremental updates — detecting new, changed, and deleted pages via content hashing — and runs automatically on a nightly cron schedule.

**Key Features:**
- Manual scraper trigger with configurable max page limit (10-500 pages)
- Automated nightly cron job at 02:00 UTC for scheduled scraping
- Incremental updates: adds new pages, re-indexes changed pages, removes deleted pages
- Content hash-based change detection to avoid unnecessary re-processing
- Recent scraping activity table showing pages scraped in the last 24 hours
- Total statistics: pages indexed and total chunks in the knowledge base
- Polite crawling with configurable request delays between page fetches
