# Key Flows

## 1. User Login
Existing users authenticate with their email and password to access the chat interface.

1. User navigates to the AdaptIQ home page and sees the login form
2. User enters their email address and password
3. User clicks 'Log in'
4. System validates credentials against the company's user database (bcrypt hash comparison)
5. On success, user is redirected to the Chat page with sidebar navigation
6. On failure, an error message is displayed (e.g., 'Invalid email or password')

## 2. User Registration
New users create an account by providing their email, password, and selecting a role (user or worker). After registration, they are automatically logged in and redirected to chat.

1. User clicks 'Register' link on the login page
2. Registration form appears with email, password, and role selection fields
3. User enters email, sets a password (minimum 6 characters), and selects role (user or worker)
4. User clicks 'Create account'
5. System creates the account with bcrypt-hashed password
6. User is automatically logged in and redirected to the Chat page

## 3. Ask a Question (Core RAG Pipeline)
The primary value flow — users ask questions in natural language and receive AI-generated answers grounded in the company's knowledge base documents and scraped web content. The answer includes source citations and a feedback mechanism.

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

## 4. Rate a Response
After receiving an AI-generated answer, users can provide feedback through a star rating and optional comment. This feedback drives the continual learning system, adjusting document relevance scores to improve future answers.

1. User receives an AI-generated response in the chat
2. User clicks 'Rate this response' expander below the answer
3. User selects a 1-5 star rating using radio buttons
4. User optionally types a comment in the text field
5. User clicks 'Submit feedback'
6. System records the feedback and triggers AI analysis of why the rating was given
7. System adjusts relevance scores of the chunks used in the answer based on EWC plasticity
8. A 'Feedback recorded' confirmation appears

## 5. Upload Knowledge Base Documents
Admins upload company documents to expand the AI assistant's knowledge base. Documents are automatically processed, chunked, embedded, and made searchable.

1. Admin navigates to the Documents section via the sidebar
2. Admin selects visibility: 'public' (all users) or 'worker' (workers and admins only)
3. Admin uses the file uploader to select one or more files (PDF, TXT, DOCX, or MD)
4. Admin clicks 'Ingest selected files'
5. System processes each file: extracts text, splits into chunks, generates embeddings
6. System indexes chunks in the vector database with appropriate visibility metadata
7. Progress bar shows processing status for each file
8. Success/error messages confirm the result (e.g., 'Indexed 45 chunks from report.pdf')
9. Newly indexed documents appear in the 'Indexed Documents' table below

## 6. Run Web Scraper
Admins manually trigger a website crawl to index or update web content in the knowledge base. The scraper incrementally detects new, changed, and deleted pages.

1. Admin navigates to the Scraper section via the sidebar
2. Admin optionally adjusts the 'Max pages' parameter (default 100, range 10-500)
3. Admin clicks 'Run scraper now'
4. System begins breadth-first crawl of the company website
5. For each page: text is extracted, chunked, embedded, and indexed
6. System compares content hashes to detect changed or deleted pages
7. Summary appears showing counts: added, updated, removed, unchanged, errors
8. Recent scraping activity table shows pages processed in the last 24 hours
9. Total indexed pages and chunks metrics are updated

## 7. Review Analytics Dashboard
Admins review usage statistics, satisfaction metrics, and continual learning health indicators to understand how the AI assistant is performing and whether the knowledge base needs attention.

1. Admin navigates to the Analytics section via the sidebar
2. Admin views request volume metrics: today, 7-day, and 30-day counts
3. Admin checks the overall satisfaction rate percentage
4. Admin reviews the Top 10 most frequently asked questions
5. Admin monitors the continual learning section: drift status, similarity, and plasticity
6. Admin reviews document relevance scores to identify underperforming content
7. Admin uses insights to decide whether to upload new documents or re-scrape the website

## 8. Review Audit Logs
Admins review encrypted audit log entries to monitor security events, including blocked toxic queries and prompt injection attempts.

1. Admin navigates to the Logs section via the sidebar
2. Admin sees the last 20 decrypted audit log entries
3. Each entry shows timestamp, event type, and toxic/safe status badge
4. Admin expands an entry to view the full decrypted JSON payload
5. Admin reviews blocked queries, reasons for blocking, and associated user IDs
6. Admin uses audit data to identify security concerns or usage patterns
