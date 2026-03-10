"""
Article Content Extractor for the Verified Medical Retrieval Pipeline.

Extracts structured medical fields from article content.
Uses LLM for field extraction ONLY — trust decisions are already made.
"""

import json
import os
from dotenv import load_dotenv

load_dotenv()


def extract_article_fields(content: str, url: str, title: str = "", llm=None) -> dict:
    """
    Extract structured medical fields from an article's content.

    If an LLM is provided, it is used for intelligent field extraction.
    Otherwise, a basic keyword-based extraction is performed.

    Returns a dict with standardized medical fields.
    """
    base_record = {
        "title": title,
        "source_link": url,
        "raw_article_text": content,
        "source": "",
        "publication_year": "",
        "medical_topic": "",
        "key_symptoms": [],
        "lab_markers": [],
        "treatments": [],
        "lifestyle_recommendations": [],
        "key_conclusions": "",
    }

    if not content or len(content) < 100:
        return base_record

    if llm:
        return _extract_with_llm(content, url, title, llm, base_record)

    return base_record


def _extract_with_llm(content: str, url: str, title: str, llm, base_record: dict) -> dict:
    """Use LLM to extract structured fields from article text."""
    prompt = f"""You are a medical data extraction assistant. Extract the following fields from the article text below.
Return ONLY valid JSON with these keys:
- source (string: publisher name)
- publication_year (string: year if found, else "")
- medical_topic (string: primary condition/topic)
- key_symptoms (list of strings)
- lab_markers (list of strings)
- treatments (list of strings)
- lifestyle_recommendations (list of strings)
- key_conclusions (string: 1-2 sentence summary)

Article Title: {title}
Article URL: {url}

Article Text (first 3000 chars):
{content[:3000]}

Return ONLY the JSON object, no markdown or explanation."""

    try:
        response = llm.invoke(prompt).content.strip()
        # Clean markdown code fences if present
        if response.startswith("```"):
            response = response.split("\n", 1)[1]
        if response.endswith("```"):
            response = response.rsplit("```", 1)[0]
        response = response.strip()

        extracted = json.loads(response)
        base_record.update(extracted)
    except Exception as e:
        print(f"[ArticleExtractor] LLM extraction failed for {url}: {e}")

    return base_record
