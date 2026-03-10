"""
Constraints Validator for the Verified Medical Retrieval Pipeline.

Applies deterministic validation rules before any data enters the knowledge base.
Designed to be lenient enough for Tavily search snippets while still filtering junk.
"""

MIN_ARTICLE_LENGTH = 80   # Tavily snippets are typically 150-400 chars
MIN_VIDEO_METADATA_LENGTH = 30


def validate(record: dict) -> dict:
    """
    Validate a single record against constraints.

    Returns:
        {"valid": bool, "reason": str}
    """
    url = record.get("url", "")
    content = record.get("content", "")
    content_type = record.get("content_type", "ARTICLE")
    confidence_level = record.get("confidence_level", "LOW")

    # Rule 1: Must have a URL
    if not url or not url.startswith("http"):
        return {"valid": False, "reason": "Missing or malformed URL"}

    # Rule 2: Confidence must be HIGH or MEDIUM (not LOW)
    if confidence_level not in ("HIGH", "MEDIUM"):
        return {"valid": False, "reason": f"Rejected confidence level: {confidence_level}"}

    # Rule 3: Content must not be empty
    if not content.strip():
        return {"valid": False, "reason": "Empty content"}

    # Rule 4: Article content minimum length (lenient for Tavily snippets)
    if content_type == "ARTICLE" and len(content.strip()) < MIN_ARTICLE_LENGTH:
        return {"valid": False, "reason": f"Article content too short ({len(content)} < {MIN_ARTICLE_LENGTH})"}

    # Rule 5: Video must have some metadata
    if content_type == "VIDEO":
        has_title = bool(record.get("title", ""))
        has_description = len(content) >= MIN_VIDEO_METADATA_LENGTH
        if not has_title and not has_description:
            return {"valid": False, "reason": "Video missing usable metadata"}

    return {"valid": True, "reason": "Passed all constraints"}


def validate_batch(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Validate a batch of records. Rejects duplicates and invalid records.

    Returns:
        (accepted, rejected) — with rejection reasons attached
    """
    accepted = []
    rejected = []
    seen_urls = set()

    for r in records:
        url = r.get("url", "")

        # Deduplication
        if url in seen_urls:
            r["rejection_reason"] = "Duplicate URL"
            rejected.append(r)
            continue
        seen_urls.add(url)

        result = validate(r)
        if result["valid"]:
            accepted.append(r)
        else:
            r["rejection_reason"] = result["reason"]
            rejected.append(r)

    print(f"[Constraints] {len(accepted)} accepted, {len(rejected)} rejected.")
    for r in rejected:
        print(f"  DROPPED: {r.get('rejection_reason')} — {r.get('url','')[:70]}")
    return accepted, rejected
