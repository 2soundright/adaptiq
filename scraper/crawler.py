"""
scraper/crawler.py
------------------
Crawls https://www.pendo.io and its subpages.
Extracts meaningful text (paragraphs) using BeautifulSoup4.
Ignores video, live-stream, and image-only pages.
All HTTP is synchronous (httpx).
"""

import hashlib
import re
import time
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

_BASE_URL      = "https://www.pendo.io"
_START_PATHS   = ["/"]
_ALLOWED_PATH  = "/"
_MAX_PAGES     = 300
_REQUEST_DELAY = 1.5   # seconds between requests (be polite)
_TIMEOUT       = 20.0

_IGNORE_PATH_PATTERNS = re.compile(
    r"/(video|videos|live|watch|stream|photo|photos|gallery|galleries|img)/",
    re.IGNORECASE,
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AIBot/1.0; "
        "+https://www.pendo.io)"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _is_allowed_url(url: str) -> bool:
    """Return True if the URL belongs to pendo.io and is not ignored."""
    try:
        parsed = urlparse(url)
        if "pendo.io" not in parsed.netloc:
            return False
        if _ALLOWED_PATH not in parsed.path:
            return False
        if _IGNORE_PATH_PATTERNS.search(parsed.path):
            return False
        return True
    except Exception:
        return False


def _extract_text(soup: BeautifulSoup) -> str:
    """
    Extract meaningful paragraph text from a parsed page.
    Removes nav, header, footer, script, style noise.
    """
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "aside", "noscript", "iframe", "form"]):
        tag.decompose()

    paragraphs: List[str] = []
    for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "li", "blockquote"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 40:        # skip very short fragments
            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def _md5(text: str) -> str:
    """Return the MD5 hash of a string."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _extract_links(soup: BeautifulSoup, current_url: str) -> List[str]:
    """Extract all internal links from the page."""
    links: List[str] = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#"):
            continue
        full_url = urljoin(current_url, href).split("?")[0].split("#")[0]
        if _is_allowed_url(full_url):
            links.append(full_url)
    return links


# ── public API ────────────────────────────────────────────────────────────────

def crawl(
    start_urls: Optional[List[str]] = None,
    max_pages: int = _MAX_PAGES,
) -> List[Dict]:
    """
    Breadth-first crawl of the target website.

    Crawls from the root by default,
    or from the provided list of start_urls.

    Returns:
        List of page dicts with keys:
            url, title, text, content_hash
    """
    if start_urls is None:
        start_urls = [f"{_BASE_URL}{path}" for path in _START_PATHS]

    visited: Set[str] = set()
    queue:   List[str] = list(start_urls)
    pages:   List[Dict] = []

    try:
        client = httpx.Client(headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
    except Exception as exc:
        print(f"[crawler] Failed to create httpx client: {exc}")
        return []

    print(f"[crawler] Starting crawl from: {start_urls}")

    try:
        while queue and len(pages) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                resp = client.get(url)
                if resp.status_code != 200:
                    continue
                content_type = resp.headers.get("content-type", "")
                if "text/html" not in content_type:
                    continue
            except Exception as exc:
                print(f"[crawler] Request failed for {url}: {exc}")
                time.sleep(_REQUEST_DELAY)
                continue

            try:
                soup  = BeautifulSoup(resp.text, "lxml")
                title = soup.title.string.strip() if soup.title else url
                text  = _extract_text(soup)

                if len(text) < 100:
                    # Skip near-empty / purely multimedia pages
                    continue

                content_hash = _md5(text)
                pages.append(
                    {
                        "url":          url,
                        "title":        title,
                        "text":         text,
                        "content_hash": content_hash,
                    }
                )

                # Enqueue newly discovered links
                for link in _extract_links(soup, url):
                    if link not in visited:
                        queue.append(link)

            except Exception as exc:
                print(f"[crawler] Parse error for {url}: {exc}")

            time.sleep(_REQUEST_DELAY)

    finally:
        client.close()

    print(f"[crawler] Crawled {len(pages)} pages total across {start_urls}")
    return pages


def fetch_page(url: str) -> Optional[Dict]:
    """
    Fetch and parse a single page.

    Returns:
        Page dict or None on failure.
    """
    if not _is_allowed_url(url):
        print(f"[crawler] URL not allowed: {url}")
        return None
    try:
        with httpx.Client(headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(url)
        if resp.status_code != 200:
            return None
        soup  = BeautifulSoup(resp.text, "lxml")
        title = soup.title.string.strip() if soup.title else url
        text  = _extract_text(soup)
        if len(text) < 100:
            return None
        return {
            "url":          url,
            "title":        title,
            "text":         text,
            "content_hash": _md5(text),
        }
    except Exception as exc:
        print(f"[crawler] fetch_page({url}) failed: {exc}")
        return None
