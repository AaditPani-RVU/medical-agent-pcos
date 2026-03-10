"""
Knowledge Ingestion Pipeline — Orchestrator.

Ties together: search → filter → classify → score → validate → extract → format.

This is the main entry point for the verified medical retrieval pipeline.
"""

import sys
import os

# Add parent paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.tavily_search import MedicalSearchEngine
from retrieval.domain_filter import filter_by_domain
from retrieval.content_classifier import classify_results
from retrieval.confidence_scoring import score_results
from retrieval.constraints_validator import validate_batch
from extraction.article_extractor import extract_article_fields
from extraction.youtube_extractor import extract_video_fields


NO_RESULTS_MESSAGE = "No verified medical sources found for this query."


class KnowledgeIngestionPipeline:
    """
    Orchestrates the full retrieval → extraction → storage pipeline.

    Pipeline flow:
        User Query
        ↓ Tavily broad search (top 20)
        ↓ Deterministic domain filtering
        ↓ Content type classification (ARTICLE / VIDEO)
        ↓ Confidence scoring
        ↓ Constraint validation
        ↓ Content extraction
        ↓ Structured output
    """

    def __init__(self, llm=None, max_results: int = 20):
        self.search_engine = MedicalSearchEngine(max_results=max_results)
        self.llm = llm

    def run(self, query: str, query_topic: str = "") -> dict:
        """
        Execute the full pipeline for a given query.

        Returns:
            {
                "articles": [structured article records],
                "videos": [structured video records],
                "context": str (for RAG),
                "source_urls": [{"url", "score", "type"}],
                "message": str (status),
            }
        """
        topic = query_topic or query
        print(f"\n{'='*60}")
        print(f"[Pipeline] Starting ingestion for: {query}")
        print(f"{'='*60}")

        # Step 1: Broad search
        raw_results = self.search_engine.search(query)
        print(f"[Pipeline] Step 1: {len(raw_results)} raw results retrieved.")

        if not raw_results:
            return self._empty_response()

        # Step 2: Domain filtering
        filtered, rejected = filter_by_domain(raw_results)
        print(f"[Pipeline] Step 2: {len(filtered)} passed domain filter.")

        if not filtered:
            return self._empty_response()

        # Step 3: Content type classification
        classified = classify_results(filtered)
        articles = [r for r in classified if r["content_type"] == "ARTICLE"]
        videos = [r for r in classified if r["content_type"] == "VIDEO"]
        print(f"[Pipeline] Step 3: {len(articles)} articles, {len(videos)} videos.")

        # Step 4: Confidence scoring
        scored = score_results(classified)
        print(f"[Pipeline] Step 4: Confidence scores assigned.")

        # Step 5: Constraint validation
        validated, val_rejected = validate_batch(scored)
        print(f"[Pipeline] Step 5: {len(validated)} passed constraints.")

        if not validated:
            return self._empty_response()

        # Step 6: Content extraction
        article_records = []
        video_records = []

        for r in validated:
            r["query_topic"] = topic

            if r["content_type"] == "ARTICLE":
                extracted = extract_article_fields(
                    content=r.get("content", ""),
                    url=r.get("url", ""),
                    title=r.get("title", ""),
                    llm=self.llm,
                )
                extracted["confidence_level"] = r.get("confidence_level", "")
                extracted["confidence_score"] = r.get("confidence_score", 0)
                extracted["content_type"] = "ARTICLE"
                extracted["query_topic"] = topic
                article_records.append(extracted)

            elif r["content_type"] == "VIDEO":
                extracted = extract_video_fields(
                    content=r.get("content", ""),
                    url=r.get("url", ""),
                    title=r.get("title", ""),
                    llm=self.llm,
                )
                extracted["confidence_level"] = r.get("confidence_level", "")
                extracted["confidence_score"] = r.get("confidence_score", 0)
                extracted["content_type"] = "VIDEO"
                extracted["query_topic"] = topic
                video_records.append(extracted)

        print(f"[Pipeline] Step 6: Extracted {len(article_records)} articles, {len(video_records)} videos.")

        # Build RAG context and source list
        context_parts = []
        source_urls = []

        for i, a in enumerate(article_records):
            context_parts.append(
                f"[Article {i+1}]: {a['source_link']} (Confidence: {a['confidence_level']})\n"
                f"Content: {a['raw_article_text'][:2000]}"
            )
            source_urls.append({
                "url": a["source_link"],
                "score": a["confidence_score"],
                "type": "article",
            })

        for i, v in enumerate(video_records):
            text = v.get("transcript") or v.get("video_description", "")
            context_parts.append(
                f"[Video {i+1}]: {v['video_url']} (Confidence: {v['confidence_level']})\n"
                f"Content: {text[:1500]}"
            )
            source_urls.append({
                "url": v["video_url"],
                "score": v["confidence_score"],
                "type": "video",
            })

        context = "\n\n".join(context_parts) if context_parts else NO_RESULTS_MESSAGE

        print(f"[Pipeline] Complete. {len(source_urls)} total verified sources.")
        print(f"{'='*60}\n")

        return {
            "articles": article_records,
            "videos": video_records,
            "context": context,
            "source_urls": source_urls,
            "message": "success",
        }

    def format_response(self, result: dict) -> str:
        """Format pipeline results into a human-readable Articles/Videos response."""
        if result.get("message") != "success":
            return NO_RESULTS_MESSAGE

        lines = []

        if result["articles"]:
            lines.append("**Articles**\n")
            for i, a in enumerate(result["articles"], 1):
                source = a.get("source", "Unknown")
                lines.append(f"{i}. {a['title']}")
                lines.append(f"   Source: {source}")
                lines.append(f"   URL: {a['source_link']}")
                lines.append("")

        if result["videos"]:
            lines.append("**Videos**\n")
            for i, v in enumerate(result["videos"], 1):
                channel = v.get("channel_name", "Unknown")
                lines.append(f"{i}. {v['video_title']}")
                lines.append(f"   Channel: {channel}")
                lines.append(f"   URL: {v['video_url']}")
                lines.append("")

        return "\n".join(lines) if lines else NO_RESULTS_MESSAGE

    def _empty_response(self) -> dict:
        print(f"[Pipeline] No verified sources found.")
        return {
            "articles": [],
            "videos": [],
            "context": NO_RESULTS_MESSAGE,
            "source_urls": [],
            "message": NO_RESULTS_MESSAGE,
        }


# --- Standalone test ---
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    except Exception:
        llm = None

    pipeline = KnowledgeIngestionPipeline(llm=llm)
    result = pipeline.run("PCOS symptoms and treatment")
    print("\n--- Formatted Response ---")
    print(pipeline.format_response(result))
