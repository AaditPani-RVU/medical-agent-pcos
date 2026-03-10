"""
Article Scraper for building the local medical knowledge base.

Uses trafilatura for clean text extraction from trusted medical websites.
Falls back to requests + BeautifulSoup for simpler pages.
"""

import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.domain_filter import is_trusted, get_domain
from retrieval.confidence_scoring import score_source


def scrape_article(url: str) -> dict | None:
    """
    Scrape a single article URL and return a structured record.

    Returns None if scraping fails or domain is not trusted.
    """
    if not is_trusted(url):
        print(f"[Scraper] Rejected untrusted domain: {url}")
        return None

    domain = get_domain(url)
    content = _extract_content(url)

    if not content or len(content) < 50:
        print(f"[Scraper] No usable content from: {url}")
        return None

    title = _extract_title(url, content)
    scoring = score_source(url, "ARTICLE")

    return {
        "title": title,
        "url": url,
        "source_domain": domain,
        "content_type": "ARTICLE",
        "content": content,
        "confidence_level": scoring["confidence_level"],
        "confidence_score": scoring["confidence_score"],
        "source_label": domain,
    }


def _extract_content(url: str) -> str:
    """Extract clean text content from a URL."""
    # Try trafilatura first (best quality)
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
            if text and len(text) > 50:
                return text
    except ImportError:
        pass
    except Exception as e:
        print(f"[Scraper] Trafilatura failed for {url}: {e}")

    # Fallback: requests + BeautifulSoup
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove script/style
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:10000]  # Cap at 10k chars
    except Exception as e:
        print(f"[Scraper] BeautifulSoup fallback failed for {url}: {e}")

    return ""


def _extract_title(url: str, content: str) -> str:
    """Extract a title from the content or URL."""
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()[:200]
    except Exception:
        pass

    # Fallback: first line of content
    first_line = content.split("\n")[0].strip()
    return first_line[:200] if first_line else url.split("/")[-1].replace("-", " ").title()


def scrape_batch(urls: list[str]) -> list[dict]:
    """Scrape multiple URLs and return list of valid records."""
    results = []
    for i, url in enumerate(urls):
        print(f"[Scraper] ({i+1}/{len(urls)}) {url[:70]}...")
        record = scrape_article(url)
        if record:
            results.append(record)
    print(f"[Scraper] Successfully scraped {len(results)}/{len(urls)} articles.")
    return results


if __name__ == "__main__":
    test_urls = [
        "https://www.mayoclinic.org/diseases-conditions/pcos/symptoms-causes/syc-20353439",
        "https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome",
        "https://www.cdc.gov/diabetes/about/pcos-and-diabetes.html",
    ]
    records = scrape_batch(test_urls)
    for r in records:
        print(f"  {r['title'][:60]} | {r['source_domain']} | {r['confidence_level']} | {len(r['content'])} chars")
