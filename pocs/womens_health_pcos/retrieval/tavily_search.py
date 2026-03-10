"""
Tavily Search Wrapper for the Verified Medical Retrieval Pipeline.

Performs broad web search using Tavily (Free Tier compatible).
No include_domains restriction — filtering happens post-retrieval.
"""

import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch

load_dotenv()


class MedicalSearchEngine:
    """Wraps Tavily search for healthcare information retrieval."""

    def __init__(self, max_results: int = 20):
        if not os.getenv("TAVILY_API_KEY"):
            raise EnvironmentError("TAVILY_API_KEY is not set.")
        self.engine = TavilySearch(max_results=max_results)

    def search(self, query: str) -> list[dict]:
        """
        Execute a broad search and return normalized results.

        Returns list of dicts with keys: title, url, content, snippet
        """
        print(f"[TavilySearch] Querying: {query}")
        raw = self.engine.invoke({"query": query})
        return self._normalize(raw)

    def _normalize(self, raw) -> list[dict]:
        """Normalize Tavily output into a consistent format."""
        results = []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                        "snippet": item.get("snippet", item.get("content", "")[:300]),
                    })
                elif isinstance(item, str):
                    results.append({"title": "", "url": item, "content": "", "snippet": ""})
        elif isinstance(raw, dict):
            # Single result or wrapped format
            if "results" in raw:
                return self._normalize(raw["results"])
            results.append({
                "title": raw.get("title", ""),
                "url": raw.get("url", ""),
                "content": raw.get("content", ""),
                "snippet": raw.get("snippet", raw.get("content", "")[:300]),
            })
        return results
