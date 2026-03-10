"""
Deterministic Confidence Scoring for the Verified Medical Retrieval Pipeline.

Assigns rule-based confidence levels to each source.
No LLM involvement — purely domain-based.
"""

from .domain_filter import get_domain

# --- Confidence Tiers ---

HIGH_CONFIDENCE_DOMAINS = [
    "who.int",
    "cdc.gov",
    "nih.gov",
    "nhs.uk",
    "mayoclinic.org",
    "clevelandclinic.org",
    "endocrine.org",
    "eshre.eu",
    "icmr.gov.in",
]

MEDIUM_CONFIDENCE_DOMAINS = [
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "monash.edu",
]

# Known verified medical YouTube channels (lowercase)
VERIFIED_VIDEO_CHANNELS = [
    "mayo clinic",
    "cleveland clinic",
    "khan academy",
    "osmosis",
    "dr. eric berg",
    "nucleus medical media",
    "animated",
    "ted-ed",
    "world health organization",
    "centers for disease control and prevention",
    "nhs",
]


def score_source(url: str, content_type: str, channel_name: str = "") -> dict:
    """
    Assign a deterministic confidence level and numeric score.

    Args:
        url: Source URL
        content_type: "ARTICLE" or "VIDEO"
        channel_name: YouTube channel name (only relevant for VIDEO)

    Returns:
        {"confidence_level": str, "confidence_score": int}
    """
    domain = get_domain(url)

    # --- Article scoring ---
    if content_type == "ARTICLE":
        if any(domain == d or domain.endswith("." + d) for d in HIGH_CONFIDENCE_DOMAINS):
            return {"confidence_level": "HIGH", "confidence_score": 95}
        if any(domain == d or domain.endswith("." + d) for d in MEDIUM_CONFIDENCE_DOMAINS):
            return {"confidence_level": "MEDIUM", "confidence_score": 75}
        return {"confidence_level": "LOW", "confidence_score": 20}

    # --- Video scoring ---
    if content_type == "VIDEO":
        if channel_name and any(v in channel_name.lower() for v in VERIFIED_VIDEO_CHANNELS):
            return {"confidence_level": "MEDIUM", "confidence_score": 82}
        # Default: still MEDIUM so videos pass constraints but lower score
        return {"confidence_level": "MEDIUM", "confidence_score": 65}

    return {"confidence_level": "LOW", "confidence_score": 0}


def score_results(results: list[dict]) -> list[dict]:
    """Add confidence_level and confidence_score to each result."""
    for r in results:
        scoring = score_source(
            url=r.get("url", ""),
            content_type=r.get("content_type", "ARTICLE"),
            channel_name=r.get("channel_name", ""),
        )
        r["confidence_level"] = scoring["confidence_level"]
        r["confidence_score"] = scoring["confidence_score"]
    return results
