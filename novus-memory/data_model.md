# Data and Content Model

## What Users Create and Manage

AdaptIQ manages several types of data entities:

### Companies
- The top-level organizational entity
- Each company has its own isolated knowledge base, users, and settings
- Configured with a name, website URL, and scraping toggle

### Users
- Belong to a company with email-based authentication
- Have one of three roles: user, worker, or admin
- Unique email per company (same email can exist in different companies)

### Documents
- Uploaded files (PDF, TXT, DOCX, MD) that form the knowledge base
- Tracked with metadata: filename, file type, size, visibility, content hash, chunk count
- Have dynamic relevance scores and usage counts that update over time

### Conversations
- Each Q&A exchange between a user and the AI assistant
- Stores the original query, full response, detected language, and source references
- Used for analytics and feedback tracking

### Feedback
- User ratings (+1/-1 score derived from 1-5 stars) with optional comments
- Linked to conversations and analyzed by LLM for quality insights
- Drives the continual learning relevance adjustments

### Scraped Pages
- Web pages crawled from the company website
- Tracked with URL, title, content hash, chunk count, and last scraped timestamp
- Supports incremental updates via hash comparison
