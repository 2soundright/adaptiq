# Upload Knowledge Base Documents

Admins upload company documents to expand the AI assistant's knowledge base. Documents are automatically processed, chunked, embedded, and made searchable.

**Persona:** Admin

1. Admin navigates to the Documents section via the sidebar
2. Admin selects visibility: 'public' (all users) or 'worker' (workers and admins only)
3. Admin uses the file uploader to select one or more files (PDF, TXT, DOCX, or MD)
4. Admin clicks 'Ingest selected files'
5. System processes each file: extracts text, splits into chunks, generates embeddings
6. System indexes chunks in the vector database with appropriate visibility metadata
7. Progress bar shows processing status for each file
8. Success/error messages confirm the result (e.g., 'Indexed 45 chunks from report.pdf')
9. Newly indexed documents appear in the 'Indexed Documents' table below
