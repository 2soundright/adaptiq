# Document Management

An admin-only area for uploading and managing knowledge base documents. Admins can upload PDF, TXT, DOCX, and Markdown files (up to 50 MB each) which are automatically parsed, chunked into segments, embedded using AI models, and indexed into the vector database. Documents can be set as 'public' (visible to all users) or 'worker' (visible only to workers and admins). The system tracks document relevance scores and usage counts that evolve over time based on user feedback.

## Key Features

- Multi-format document upload: PDF, TXT, DOCX, and Markdown
- 50 MB file size limit with batch upload support
- Automatic text extraction, chunking, embedding, and vector indexing
- Visibility control: public (all users) or worker (workers and admins only)
- Document relevance scoring that adapts based on user feedback
- Usage tracking showing how often each document's content is retrieved
- Indexed documents table showing files, relevance scores, and usage counts
