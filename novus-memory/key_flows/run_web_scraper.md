# Run Web Scraper

Admins manually trigger a website crawl to index or update web content in the knowledge base. The scraper incrementally detects new, changed, and deleted pages.

**Persona:** Admin

1. Admin navigates to the Scraper section via the sidebar
2. Admin optionally adjusts the 'Max pages' parameter (default 100, range 10-500)
3. Admin clicks 'Run scraper now'
4. System begins breadth-first crawl of the company website (e.g., pendo.io)
5. For each page: text is extracted, chunked, embedded, and indexed
6. System compares content hashes to detect changed or deleted pages
7. Summary appears showing counts: added, updated, removed, unchanged, errors
8. Recent scraping activity table shows pages processed in the last 24 hours
9. Total indexed pages and chunks metrics are updated
