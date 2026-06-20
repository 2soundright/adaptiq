# AdaptIQ — Product Documentation

> AI-powered knowledge base assistant with RAG + continual learning

## Table of Contents

- [Product Overview](#product-overview)
- [User Personas](#user-personas)
- [Product Areas](#product-areas)
- [Key Flows](#key-flows)
- [Integrations](#integrations)
- [Documentation](#documentation)
  - [RAG Pipeline Architecture](#rag-pipeline-architecture)
  - [Continual Learning System](#continual-learning-system)
  - [Multilingual Support](#multilingual-support)
  - [Security and Safety](#security-and-safety)
  - [Content Visibility and Access Control](#content-visibility-and-access-control)
  - [Data and Content Model](#data-and-content-model)
- [Site Map](#site-map)

---

## Product Overview

AdaptIQ is an AI-powered knowledge base assistant built for companies and organizations that want to provide intelligent, context-aware Q&A support to their teams. It combines Retrieval-Augmented Generation (RAG) with continual learning to deliver accurate, document-grounded answers that improve over time based on user feedback.

The product solves the problem of making organizational knowledge — stored across documents, internal files, and company websites — instantly accessible through a conversational interface. Rather than searching through PDFs, documentation pages, or help articles, users simply ask questions in natural language and receive AI-generated answers backed by source citations.

AdaptIQ supports three languages (English, Russian, and Kazakh), features role-based content access control, and includes built-in safety mechanisms to detect and block toxic or malicious queries. It is designed for multi-tenant use, with company-level data isolation.

The product is built as a Streamlit web application with a polished, responsive UI that works across desktop and mobile devices.

---

## User Personas

### Admin
The system administrator who manages the AI assistant's knowledge base, monitors usage analytics, reviews security logs, and configures the web scraper. Has full access to all features including the admin panel.

**Permissions:**
- Access the Chat interface to ask questions
- Upload and manage knowledge base documents (PDF, TXT, DOCX, MD)
- Set document visibility (public or worker-only)
- View usage analytics: request counts, satisfaction rates, top questions
- Monitor continual learning metrics: drift detection, plasticity curves
- Review and decrypt audit log entries
- Manually trigger the web scraper and configure scraping parameters
- View all indexed documents and their relevance scores
- Access the full admin sidebar with all navigation sections

### Worker
An internal team member who has access to both public and internal (worker-level) knowledge base content. Workers can ask questions and receive answers that may include internal documentation not available to regular users.

**Permissions:**
- Access the Chat interface to ask questions
- Retrieve answers from both public AND worker-only document collections
- Rate responses and provide feedback
- View source citations and excerpts from internal documents
- Cannot access the admin panel (Documents, Analytics, Scraper, or Logs)

### User
A regular end-user who can ask questions and receive answers from the public knowledge base. Users only have access to publicly-visible documents and scraped web content.

**Permissions:**
- Access the Chat interface to ask questions
- Retrieve answers from public document collections only
- Rate responses and provide feedback
- View source citations and excerpts from public documents
- Cannot access the admin panel or worker-only content

---

## Product Areas

### Authentication
Handles user login, registration, and session management. Users authenticate with email and password, and are associated with a specific company. The system supports three roles (user, worker, admin) which determine access to different features and content collections. Passwords are securely hashed with bcrypt.

**Key Features:**
- Email and password login with bcrypt-hashed credential verification
- Self-service registration with role selection (user or worker)
- Role-based access control: user, worker, and admin roles
- Company-scoped authentication — users belong to a specific company
- Automatic session management with login persistence and logout
- Default admin and user accounts seeded on first database initialization

### Chat
The core product experience — a conversational AI interface where users ask questions and receive intelligent, document-grounded answers. Each query passes through an 8-step RAG pipeline: safety check, language detection, query transformation, embedding, retrieval, reranking, streaming response generation, and feedback collection.

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

### Document Management
An admin-only area for uploading and managing knowledge base documents. Admins can upload PDF, TXT, DOCX, and Markdown files (up to 50 MB each) which are automatically parsed, chunked, embedded, and indexed into the vector database.

**Key Features:**
- Multi-format document upload: PDF, TXT, DOCX, and Markdown
- 50 MB file size limit with batch upload support
- Automatic text extraction, chunking, embedding, and vector indexing
- Visibility control: public (all users) or worker (workers and admins only)
- Document relevance scoring that adapts based on user feedback
- Usage tracking showing how often each document's content is retrieved
- Indexed documents table showing files, relevance scores, and usage counts

### Analytics
An admin-only dashboard providing usage statistics, satisfaction metrics, continual learning health indicators, and document performance scores.

**Key Features:**
- Request volume metrics: today, 7-day, and 30-day conversation counts
- User satisfaction rate calculated from feedback scores
- Top 10 most frequently asked questions with occurrence counts
- Continual learning dashboard: drift status, similarity metrics, and plasticity curve
- Document relevance scores showing which documents perform best
- Drift detection status indicating whether query patterns are shifting

### Audit Logs
An admin-only security monitoring area that displays encrypted audit log entries. All sensitive events are logged with encrypted payloads using Fernet symmetric encryption.

**Key Features:**
- Last 20 audit log entries displayed with decrypted payloads
- Toxic/safe status badges for each log entry (red TOXIC vs green OK)
- Fernet-encrypted payload storage for security compliance
- Event type classification (e.g., safety_block events)
- User ID and timestamp tracking for each audit event
- Expandable detail view with full JSON payload for each entry

### Web Scraper
An admin-only tool for automatically crawling and indexing a company's website content into the knowledge base. Supports incremental updates and runs automatically on a nightly cron schedule.

**Key Features:**
- Manual scraper trigger with configurable max page limit (10-500 pages)
- Automated nightly cron job at 02:00 UTC for scheduled scraping
- Incremental updates: adds new pages, re-indexes changed pages, removes deleted pages
- Content hash-based change detection to avoid unnecessary re-processing
- Recent scraping activity table showing pages scraped in the last 24 hours
- Total statistics: pages indexed and total chunks in the knowledge base
- Polite crawling with configurable request delays between page fetches

---

## Key Flows

### 1. User Login
Existing users authenticate with their email and password to access the chat interface.

1. User navigates to the AdaptIQ home page and sees the login form
2. User enters their email address and password
3. User clicks 'Log in'
4. System validates credentials against the company's user database (bcrypt hash comparison)
5. On success, user is redirected to the Chat page with sidebar navigation
6. On failure, an error message is displayed (e.g., 'Invalid email or password')

### 2. User Registration
New users create an account by providing their email, password, and selecting a role.

1. User clicks 'Register' link on the login page
2. Registration form appears with email, password, and role selection fields
3. User enters email, sets a password (minimum 6 characters), and selects role (user or worker)
4. User clicks 'Create account'
5. System creates the account with bcrypt-hashed password
6. User is automatically logged in and redirected to the Chat page

### 3. Ask a Question (Core RAG Pipeline)
The primary value flow — users ask questions and receive AI-generated answers grounded in the company's knowledge base.

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

### 4. Rate a Response
After receiving an AI-generated answer, users can provide feedback through a star rating and optional comment.

1. User receives an AI-generated response in the chat
2. User clicks 'Rate this response' expander below the answer
3. User selects a 1-5 star rating using radio buttons
4. User optionally types a comment in the text field
5. User clicks 'Submit feedback'
6. System records the feedback and triggers AI analysis of why the rating was given
7. System adjusts relevance scores of the chunks used in the answer based on EWC plasticity
8. A 'Feedback recorded' confirmation appears

### 5. Upload Knowledge Base Documents
Admins upload company documents to expand the AI assistant's knowledge base.

1. Admin navigates to the Documents section via the sidebar
2. Admin selects visibility: 'public' (all users) or 'worker' (workers and admins only)
3. Admin uses the file uploader to select one or more files (PDF, TXT, DOCX, or MD)
4. Admin clicks 'Ingest selected files'
5. System processes each file: extracts text, splits into chunks, generates embeddings
6. System indexes chunks in the vector database with appropriate visibility metadata
7. Progress bar shows processing status for each file
8. Success/error messages confirm the result (e.g., 'Indexed 45 chunks from report.pdf')
9. Newly indexed documents appear in the 'Indexed Documents' table below

### 6. Run Web Scraper
Admins manually trigger a website crawl to index or update web content in the knowledge base.

1. Admin navigates to the Scraper section via the sidebar
2. Admin optionally adjusts the 'Max pages' parameter (default 100, range 10-500)
3. Admin clicks 'Run scraper now'
4. System begins breadth-first crawl of the company website
5. For each page: text is extracted, chunked, embedded, and indexed
6. System compares content hashes to detect changed or deleted pages
7. Summary appears showing counts: added, updated, removed, unchanged, errors
8. Recent scraping activity table shows pages processed in the last 24 hours
9. Total indexed pages and chunks metrics are updated

### 7. Review Analytics Dashboard
Admins review usage statistics, satisfaction metrics, and continual learning health indicators.

1. Admin navigates to the Analytics section via the sidebar
2. Admin views request volume metrics: today, 7-day, and 30-day counts
3. Admin checks the overall satisfaction rate percentage
4. Admin reviews the Top 10 most frequently asked questions
5. Admin monitors the continual learning section: drift status, similarity, and plasticity
6. Admin reviews document relevance scores to identify underperforming content
7. Admin uses insights to decide whether to upload new documents or re-scrape the website

### 8. Review Audit Logs
Admins review encrypted audit log entries to monitor security events.

1. Admin navigates to the Logs section via the sidebar
2. Admin sees the last 20 decrypted audit log entries
3. Each entry shows timestamp, event type, and toxic/safe status badge
4. Admin expands an entry to view the full decrypted JSON payload
5. Admin reviews blocked queries, reasons for blocking, and associated user IDs
6. Admin uses audit data to identify security concerns or usage patterns

---

## Integrations

### Groq
Powers the core AI capabilities including response generation (LLM streaming), content safety classification, query transformation/expansion, and feedback analysis. Uses multiple models: a large model for generation, a smaller model for query transformation and feedback analysis, and a safety-specific model for content moderation.

### HuggingFace Inference API
Provides two key AI services: (1) text embeddings via BAAI/bge-m3 for converting queries and documents into vector representations for semantic search, and (2) cross-encoder reranking via BAAI/bge-reranker-large for refining retrieval results. Both services have local fallback models if the API is unavailable.

### ChromaDB
Serves as the vector database for storing and searching document embeddings. Maintains separate collections per company and role (public vs worker) for content isolation. Supports cosine similarity search for semantic retrieval of relevant document chunks.

---

## Documentation

### RAG Pipeline Architecture

Every user query passes through an 8-step pipeline before an answer is generated:

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

---

### Continual Learning System

AdaptIQ features a continual learning system that automatically adapts the knowledge base based on user interactions and feedback.

#### Feedback-Driven Relevance
- When users rate responses, the system adjusts the **relevance score** of the document chunks that contributed to that answer
- Positive feedback (3+ stars) increases chunk relevance; negative feedback decreases it
- The adjustment magnitude is controlled by **plasticity** — a value that determines how responsive each chunk is to new feedback

#### Elastic Weight Consolidation (EWC)
- **New/untested chunks** have high plasticity and adapt quickly to feedback
- **Well-established chunks** (high usage count) have low plasticity and change slowly
- This prevents a single piece of bad feedback from degrading well-validated knowledge

#### Drift Detection
- Compares recent query embeddings against historical ones using cosine similarity
- If the average similarity drops below a threshold (0.7), **concept drift** is detected
- During drift, plasticity is boosted by 50% so the knowledge base can adapt faster to new topics

#### Replay Buffer
- The last 500 Q&A pairs are stored with their embeddings
- Feeds the drift detection system and can be sampled for future model updates
- Automatically prunes old entries to maintain a fixed size

---

### Multilingual Support

| Language | Code | Coverage |
|----------|------|----------|
| English | en | Full support — default language |
| Russian | ru | Full support — auto-detected from Cyrillic text |
| Kazakh | kk | Full support — auto-detected |

- **Automatic detection** via `langdetect` library
- **Response matching** — AI responds in the same language as the question
- **Safety messages** localized in all three languages
- **Query expansion** preserves the original language

---

### Security and Safety

#### Content Safety
- LLM-based safety classifier screens every query before processing
- Detects toxic language, harmful requests, jailbreak attempts, and prompt injection
- All safety blocks logged to the encrypted audit trail

#### Prompt Injection Defense
- Known injection patterns stripped at the query transformation stage
- Regex-based filter removes injection phrases before they reach retrieval
- Safety classifier provides a second line of defense at the LLM level

#### Encrypted Audit Logging
- All sensitive events logged with **Fernet symmetric encryption**
- Payloads encrypted before storage, decrypted only when viewed by admins

#### Authentication Security
- Passwords hashed with **bcrypt** (12 rounds)
- Company-scoped user isolation
- Role-based access control enforced at both UI and data layer

---

### Content Visibility and Access Control

| Role | Public Content | Worker Content | Admin Panel |
|------|---------------|----------------|-------------|
| User | ✅ | ❌ | ❌ |
| Worker | ✅ | ✅ | ❌ |
| Admin | ✅ | ✅ | ✅ |

- Each company has separate vector DB collections: `company_{id}_public` and `company_{id}_worker`
- All scraped web content is indexed as public by default
- Admins choose visibility level when uploading documents

---

### Data and Content Model

| Entity | Description |
|--------|-------------|
| **Companies** | Top-level org entity with isolated knowledge base, users, and settings |
| **Users** | Belong to a company, have one of three roles (user/worker/admin) |
| **Documents** | Uploaded files tracked with metadata, relevance scores, and usage counts |
| **Conversations** | Each Q&A exchange with query, response, language, and source refs |
| **Feedback** | User ratings linked to conversations, drives continual learning |
| **Scraped Pages** | Web pages with URL, content hash, chunk count, last scraped timestamp |

---

## Site Map

```
Login / Register Page
├── Chat Page
│   ├── Welcome Screen
│   ├── Ask a Question → Safety Check → AI Response with Sources → Rate Response
│   └── Admin Panel (Admin only)
│       ├── Documents
│       │   ├── Upload PDF / TXT / DOCX / MD
│       │   └── View Indexed Documents
│       ├── Analytics Dashboard
│       │   ├── Request Counts
│       │   ├── Satisfaction Rate
│       │   ├── Top 10 Questions
│       │   ├── Continual Learning Metrics
│       │   └── Document Relevance Scores
│       ├── Web Scraper
│       │   ├── Run Scraper Now
│       │   ├── Recent Activity
│       │   └── Total Pages and Chunks
│       └── Audit Logs
│           ├── Decrypted Log Entries
│           └── Toxic / Safe Status
└── Log Out
```
