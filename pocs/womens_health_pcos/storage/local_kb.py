"""
Local Knowledge Base for the Verified Medical Retrieval Pipeline.

SQLite-backed storage for scraped and cached trusted medical content.
Acts as the primary retrieval layer before Tavily fallback.
"""

import sqlite3
import os
import json
from datetime import datetime


DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "knowledge_base.db")


def _get_conn() -> sqlite3.Connection:
    """Get a database connection, creating the DB and tables if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            source_domain TEXT NOT NULL,
            content_type TEXT NOT NULL DEFAULT 'ARTICLE',
            content TEXT NOT NULL,
            confidence_level TEXT DEFAULT 'MEDIUM',
            confidence_score INTEGER DEFAULT 70,
            query_topics TEXT DEFAULT '',
            source_label TEXT DEFAULT '',
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(source_domain)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(content_type)
    """)
    conn.commit()
    return conn


def store(record: dict) -> bool:
    """
    Store a single source record. Deduplicates on URL.

    Returns True if stored, False if duplicate.
    """
    conn = _get_conn()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO sources
            (title, url, source_domain, content_type, content,
             confidence_level, confidence_score, query_topics, source_label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get("title", ""),
            record.get("url", ""),
            record.get("source_domain", ""),
            record.get("content_type", "ARTICLE"),
            record.get("content", ""),
            record.get("confidence_level", "MEDIUM"),
            record.get("confidence_score", 70),
            record.get("query_topics", ""),
            record.get("source_label", ""),
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def store_batch(records: list[dict]) -> int:
    """Store multiple records. Returns count of newly stored."""
    stored = 0
    for r in records:
        if store(r):
            stored += 1
    return stored


def search(query: str, limit: int = 10) -> list[dict]:
    """
    Search the local KB by keyword matching across title and content.

    Uses SQLite LIKE for simplicity. Returns list of dicts.
    """
    conn = _get_conn()
    keywords = query.lower().split()

    if not keywords:
        conn.close()
        return []

    # Build WHERE clause: all keywords must appear in title OR content
    conditions = []
    params = []
    for kw in keywords[:5]:  # Limit to 5 keywords
        conditions.append("(LOWER(title) LIKE ? OR LOWER(content) LIKE ? OR LOWER(query_topics) LIKE ?)")
        params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])

    where = " AND ".join(conditions)

    rows = conn.execute(f"""
        SELECT * FROM sources
        WHERE {where}
        ORDER BY confidence_score DESC
        LIMIT ?
    """, params + [limit]).fetchall()

    conn.close()

    results = []
    for row in rows:
        results.append({
            "title": row["title"],
            "url": row["url"],
            "source_domain": row["source_domain"],
            "content_type": row["content_type"],
            "content": row["content"],
            "confidence_level": row["confidence_level"],
            "confidence_score": row["confidence_score"],
            "source_label": row["source_label"],
        })

    return results


def count() -> int:
    """Return total number of sources in the KB."""
    conn = _get_conn()
    result = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    conn.close()
    return result


def get_all_domains() -> list[str]:
    """Return list of unique domains in the KB."""
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT source_domain FROM sources").fetchall()
    conn.close()
    return [r[0] for r in rows]
