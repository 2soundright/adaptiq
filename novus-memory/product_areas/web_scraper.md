# Web Scraper

An admin-only tool for automatically crawling and indexing a company's website content into the knowledge base. The scraper performs breadth-first crawling of the configured company website, extracts meaningful text from pages, chunks and embeds the content, and stores it in the vector database. It supports incremental updates — detecting new, changed, and deleted pages via content hashing — and runs automatically on a nightly cron schedule.

## Key Features

- Manual scraper trigger with configurable max page limit (10-500 pages)
- Automated nightly cron job at 02:00 UTC for scheduled scraping
- Incremental updates: adds new pages, re-indexes changed pages, removes deleted pages
- Content hash-based change detection to avoid unnecessary re-processing
- Recent scraping activity table showing pages scraped in the last 24 hours
- Total statistics: pages indexed and total chunks in the knowledge base
- Polite crawling with configurable request delays between page fetches
