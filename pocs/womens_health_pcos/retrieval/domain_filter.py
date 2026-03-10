"""
Deterministic Domain Filter for the Verified Medical Retrieval Pipeline.

Filters search results against a strict allowlist of trusted healthcare domains.
No LLM involvement — purely rule-based.
"""

from urllib.parse import urlparse


ALLOWED_DOMAINS = [
    # International health orgs
    "who.int",
    "cdc.gov",
    "nih.gov",
    "nhs.uk",
    # Clinical institutions
    "mayoclinic.org",
    "clevelandclinic.org",
    # Specialty orgs
    "endocrine.org",
    "eshre.eu",
    # Research databases
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    # Academic
    "monash.edu",
    # India-specific
    "icmr.gov.in",
    # Video platforms (filtered further by confidence scoring)
    "youtube.com",
    "youtu.be",
]


def get_domain(url: str) -> str:
    """Extract and normalize domain from a URL."""
    domain = urlparse(url).netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def is_trusted(url: str) -> bool:
    """Check if a URL's domain matches the allowlist (exact or subdomain)."""
    domain = get_domain(url)
    return any(domain == d or domain.endswith("." + d) for d in ALLOWED_DOMAINS)


def filter_by_domain(results: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Filter a list of search results by domain allowlist.

    Returns:
        (accepted, rejected) — two lists of result dicts
    """
    accepted = []
    rejected = []
    for r in results:
        url = r.get("url", "")
        if is_trusted(url):
            r["source_domain"] = get_domain(url)
            accepted.append(r)
        else:
            rejected.append(r)

    print(f"[DomainFilter] {len(accepted)} accepted, {len(rejected)} rejected.")
    return accepted, rejected
