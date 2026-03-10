"""
Seed the local knowledge base with trusted medical content.

Usage:
    python seed_kb.py                    # Seed with default PCOS URLs
    python seed_kb.py --topic "diabetes" # Seed with custom topic URLs
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.article_scraper import scrape_batch as scrape_articles
from ingestion.youtube_scraper import scrape_batch as scrape_videos
from storage.local_kb import store_batch, count


# Default seed URLs for PCOS knowledge base
DEFAULT_ARTICLE_URLS = [
    "https://www.mayoclinic.org/diseases-conditions/pcos/symptoms-causes/syc-20353439",
    "https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome",
    "https://www.nhs.uk/conditions/polycystic-ovary-syndrome-pcos/",
    "https://www.cdc.gov/diabetes/about/pcos-and-diabetes.html",
    "https://my.clevelandclinic.org/health/diseases/8316-polycystic-ovary-syndrome-pcos",
    "https://www.endocrine.org/patient-engagement/endocrine-library/pcos",
    "https://pubmed.ncbi.nlm.nih.gov/35255175/",
    "https://www.mayoclinic.org/diseases-conditions/pcos/diagnosis-treatment/drc-20353443",
    "https://www.nhs.uk/conditions/polycystic-ovary-syndrome-pcos/treatment/",
    "https://www.nichd.nih.gov/health/topics/pcos",
]

DEFAULT_VIDEO_URLS = [
    "https://www.youtube.com/watch?v=Gn7GmF8Wa1o",  # Cleveland Clinic PCOS
    "https://www.youtube.com/watch?v=R1mHiIqU0Gw",  # Mayo Clinic PCOS
]


def seed(article_urls: list[str] = None, video_urls: list[str] = None, topic: str = "PCOS"):
    """Scrape and store content into the local KB."""
    article_urls = article_urls or DEFAULT_ARTICLE_URLS
    video_urls = video_urls or DEFAULT_VIDEO_URLS

    print(f"\n{'='*60}")
    print(f"[Seed KB] Seeding local knowledge base for topic: {topic}")
    print(f"  Articles to scrape: {len(article_urls)}")
    print(f"  Videos to scrape: {len(video_urls)}")
    print(f"{'='*60}\n")

    # Scrape articles
    print("[Phase 1: Articles]")
    article_records = scrape_articles(article_urls)
    for r in article_records:
        r["query_topics"] = topic

    # Scrape videos
    print("\n[Phase 2: Videos]")
    video_records = scrape_videos(video_urls)
    for r in video_records:
        r["query_topics"] = topic

    # Store
    all_records = article_records + video_records
    stored = store_batch(all_records)

    print(f"\n{'='*60}")
    print(f"[Seed KB] Complete!")
    print(f"  Scraped: {len(all_records)} sources")
    print(f"  Stored: {stored} new sources")
    print(f"  Total in KB: {count()}")
    print(f"{'='*60}\n")

    return stored


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the medical knowledge base")
    parser.add_argument("--topic", default="PCOS", help="Topic label for stored content")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

    seed(topic=args.topic)
