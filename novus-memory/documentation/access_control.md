# Content Visibility and Access Control

## How Content Access Works

AdaptIQ uses a two-tier content visibility system that controls which documents are accessible to different user roles:

### Visibility Levels
- **Public**: Content is accessible to all authenticated users (users, workers, and admins). This includes scraped website content and documents marked as public during upload.
- **Worker**: Content is only accessible to users with the worker or admin role. This is intended for internal documentation, SOPs, or sensitive company knowledge.

### How It Works Technically
- Each company has separate vector database collections: `company_{id}_public` and `company_{id}_worker`
- When a **regular user** asks a question, only the public collection is searched
- When a **worker** asks a question, only the worker collection is searched
- When an **admin** asks a question, the public collection is searched
- All scraped web content is indexed as public by default
- Admins choose the visibility level when uploading documents

This ensures that internal knowledge is protected while still being available to the right team members.
