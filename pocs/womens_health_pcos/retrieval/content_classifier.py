"""
Content Type Classifier for the Verified Medical Retrieval Pipeline.

Classifies each search result as ARTICLE or VIDEO based on domain.
Deterministic — no LLM calls.
"""

from .domain_filter import get_domain

VIDEO_DOMAINS = ["youtube.com", "youtu.be"]


def classify(url: str) -> str:
    """
    Classify a URL as ARTICLE or VIDEO.

    Returns "VIDEO" if domain is youtube.com or youtu.be, else "ARTICLE".
    """
    domain = get_domain(url)
    if any(domain == d or domain.endswith("." + d) for d in VIDEO_DOMAINS):
        return "VIDEO"
    return "ARTICLE"


def classify_results(results: list[dict]) -> list[dict]:
    """
    Add content_type field to each result.

    Mutates and returns the same list with 'content_type' key added.
    """
    for r in results:
        r["content_type"] = classify(r.get("url", ""))
    return results
