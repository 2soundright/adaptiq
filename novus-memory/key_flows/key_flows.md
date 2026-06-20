# Key Flows

Core user flows and workflows in AdaptIQ.

| NAME | DESCRIPTION |
|------|-------------|
| [User Login](user_login.md) | Existing users authenticate with their email and password to access the chat interface. The system validates credentials against the company-scoped user database. |
| [User Registration](user_registration.md) | New users create an account by providing their email, password, and selecting a role (user or worker). After registration, they are automatically logged in and redirected to chat. |
| [Ask a Question (Core RAG Pipeline)](ask_a_question.md) | The primary value flow — users ask questions in natural language and receive AI-generated answers grounded in the company's knowledge base documents and scraped web content. The answer includes source citations and a feedback mechanism. |
| [Rate a Response](rate_a_response.md) | After receiving an AI-generated answer, users can provide feedback through a star rating and optional comment. This feedback drives the continual learning system, adjusting document relevance scores to improve future answers. |
| [Upload Knowledge Base Documents](upload_documents.md) | Admins upload company documents to expand the AI assistant's knowledge base. Documents are automatically processed, chunked, embedded, and made searchable. |
| [Run Web Scraper](run_web_scraper.md) | Admins manually trigger a website crawl to index or update web content in the knowledge base. The scraper incrementally detects new, changed, and deleted pages. |
| [Review Analytics Dashboard](review_analytics.md) | Admins review usage statistics, satisfaction metrics, and continual learning health indicators to understand how the AI assistant is performing and whether the knowledge base needs attention. |
| [Review Audit Logs](review_audit_logs.md) | Admins review encrypted audit log entries to monitor security events, including blocked toxic queries and prompt injection attempts. |
