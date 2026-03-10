"""
YouTube Video Extractor for the Verified Medical Retrieval Pipeline.

Extracts structured metadata from YouTube video search results.
Attempts transcript extraction if youtube_transcript_api is available.
"""

import re
import json


def extract_video_fields(content: str, url: str, title: str = "", llm=None) -> dict:
    """
    Extract structured fields from a YouTube video result.

    Returns a dict with video-specific metadata fields.
    """
    video_id = _extract_video_id(url)

    record = {
        "video_title": title,
        "channel_name": "",
        "video_url": url,
        "video_id": video_id,
        "video_description": content,
        "published_date": "",
        "medical_topic": "",
        "video_summary": "",
        "transcript": "",
    }

    # Try to get transcript
    transcript = _get_transcript(video_id)
    if transcript:
        record["transcript"] = transcript

    # Use LLM to extract structured fields if available
    if llm:
        source_text = transcript if transcript else content
        if source_text and len(source_text) > 50:
            record = _extract_with_llm(source_text, url, title, llm, record)

    return record


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


def _get_transcript(video_id: str) -> str:
    """Attempt to fetch YouTube transcript. Returns empty string on failure."""
    if not video_id:
        return ""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript_list])
    except Exception:
        return ""


def _extract_with_llm(text: str, url: str, title: str, llm, record: dict) -> dict:
    """Use LLM to extract structured fields from video text/transcript."""
    prompt = f"""You are a medical data extraction assistant. Extract the following fields from this video content.
Return ONLY valid JSON with these keys:
- channel_name (string)
- medical_topic (string: primary condition/topic)
- video_summary (string: 2-3 sentence summary)
- published_date (string: date if found, else "")

Video Title: {title}
Video URL: {url}

Content (first 3000 chars):
{text[:3000]}

Return ONLY the JSON object, no markdown or explanation."""

    try:
        response = llm.invoke(prompt).content.strip()
        if response.startswith("```"):
            response = response.split("\n", 1)[1]
        if response.endswith("```"):
            response = response.rsplit("```", 1)[0]
        response = response.strip()

        extracted = json.loads(response)
        record.update(extracted)
    except Exception as e:
        print(f"[YouTubeExtractor] LLM extraction failed for {url}: {e}")

    return record
