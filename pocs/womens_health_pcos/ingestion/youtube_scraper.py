"""
YouTube Video Scraper for building the local medical knowledge base.

Uses yt-dlp for metadata and youtube-transcript-api for transcripts.
"""

import os
import sys
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.confidence_scoring import score_source


def scrape_video(url: str) -> dict | None:
    """
    Scrape metadata from a YouTube video URL.

    Returns structured record or None on failure.
    """
    video_id = _extract_video_id(url)
    if not video_id:
        print(f"[YTScraper] Could not extract video ID from: {url}")
        return None

    metadata = _get_metadata_ytdlp(url)
    if not metadata:
        metadata = {"title": "", "channel": "", "description": "", "url": url}

    transcript = _get_transcript(video_id)

    content = transcript if transcript else metadata.get("description", "")
    title = metadata.get("title", "")
    channel = metadata.get("channel", "")

    scoring = score_source(url, "VIDEO", channel)

    return {
        "title": title,
        "url": url,
        "source_domain": "youtube.com",
        "content_type": "VIDEO",
        "content": content[:8000],
        "confidence_level": scoring["confidence_level"],
        "confidence_score": scoring["confidence_score"],
        "source_label": f"YouTube — {channel}" if channel else "YouTube",
        "channel_name": channel,
        "video_id": video_id,
    }


def _extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def _get_metadata_ytdlp(url: str) -> dict | None:
    """Get video metadata using yt-dlp."""
    try:
        import subprocess
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "title": data.get("title", ""),
                "channel": data.get("channel", data.get("uploader", "")),
                "description": data.get("description", ""),
                "url": url,
                "upload_date": data.get("upload_date", ""),
            }
    except Exception as e:
        print(f"[YTScraper] yt-dlp failed: {e}")
    return None


def _get_transcript(video_id: str) -> str:
    """Get transcript using youtube-transcript-api."""
    if not video_id:
        return ""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript_list])
    except Exception:
        return ""


def scrape_batch(urls: list[str]) -> list[dict]:
    """Scrape multiple YouTube URLs."""
    results = []
    for i, url in enumerate(urls):
        print(f"[YTScraper] ({i+1}/{len(urls)}) {url[:70]}...")
        record = scrape_video(url)
        if record:
            results.append(record)
    print(f"[YTScraper] Successfully scraped {len(results)}/{len(urls)} videos.")
    return results


if __name__ == "__main__":
    test_urls = [
        "https://www.youtube.com/watch?v=example",
    ]
    records = scrape_batch(test_urls)
    for r in records:
        print(f"  {r['title'][:60]} | {r['channel_name']} | {len(r['content'])} chars")
