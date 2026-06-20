# Personas

## Admin
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

## Worker
An internal team member who has access to both public and internal (worker-level) knowledge base content. Workers can ask questions and receive answers that may include internal documentation not available to regular users.

**Permissions:**
- Access the Chat interface to ask questions
- Retrieve answers from both public AND worker-only document collections
- Rate responses and provide feedback
- View source citations and excerpts from internal documents
- Cannot access the admin panel (Documents, Analytics, Scraper, or Logs)

## User
A regular end-user who can ask questions and receive answers from the public knowledge base.

**Permissions:**
- Access the Chat interface to ask questions
- Retrieve answers from public document collections only
- Rate responses and provide feedback
- View source citations and excerpts from public documents
- Cannot access the admin panel or worker-only content
