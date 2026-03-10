"""
Ingests Community Reports mapping ancedotal experiences (Reddit/Quora-style data).
Stores extracted sentiments and outcomes into `community_reports`.
These sources MUST be assigned a LOW confidence score (e.g., 30)
to ensure they are treated as anecdotal, not medical fact.
"""

import sys
import os
import json

# Add root project path to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from pocs.womens_health_pcos.database.session import SessionLocal, init_db
from pocs.womens_health_pcos.database.models import CommunityReport

# Mocked community data simulating a Reddit/Forum scrape
MOCK_REDDIT_DATA = [
    {
        "title": "What actually helped your PCOS fatigue?",
        "source_domain": "reddit.com",
        "source_link": "https://reddit.com/r/PCOS/comments/mock1",
        "text_content": "I was sleeping 10 hours a day and still exhausted. I started taking Ovasitol (Inositol) and focusing on 30g protein at breakfast. Within 3 weeks my energy came back.",
        "symptom": "Fatigue",
        "treatment": "Ovasitol / Myo-inositol supplement",
        "medication": "None",
        "lifestyle_change": "High protein breakfast",
        "reported_outcome": "Improved energy levels",
        "sentiment": "Positive"
    },
    {
        "title": "Metformin side effects are brutal",
        "source_domain": "reddit.com",
        "source_link": "https://reddit.com/r/PCOSloseit/comments/mock2",
        "text_content": "Has anyone else had terrible stomach issues on 1000mg Metformin? It's been 2 weeks and I can barely leave the house. Is extended release better?",
        "symptom": "Insulin Resistance",
        "treatment": "Metformin",
        "medication": "Metformin 1000mg",
        "lifestyle_change": "None",
        "reported_outcome": "Severe GI side effects",
        "sentiment": "Negative"
    },
    {
        "title": "Hair loss finally stopping after 2 years",
        "source_domain": "reddit.com",
        "source_link": "https://reddit.com/r/womenshealth/comments/mock3",
        "text_content": "Just wanted to share a win. My hair was thinning so bad at the crown. Spironolactone 100mg plus rosemary oil massages finally stopped the shedding. It took 6 months to see a difference.",
        "symptom": "Hair loss / Alopecia",
        "treatment": "Spironolactone + Rosemary Oil",
        "medication": "Spironolactone 100mg",
        "lifestyle_change": "Rosemary oil massages",
        "reported_outcome": "Shedding stopped",
        "sentiment": "Positive"
    }
]

def run_ingestion():
    init_db()
    print("Starting Community Experience Ingestion...")
    db = SessionLocal()
    total_stored = 0
    try:
        # In a real app, instantiate PRAW (Reddit API) here and fetch top posts from r/PCOS
        for post in MOCK_REDDIT_DATA:
            exists = db.query(CommunityReport).filter(CommunityReport.source_link == post["source_link"]).first()
            if not exists:
                record = CommunityReport(
                    title=post["title"],
                    source_domain=post["source_domain"],
                    text_content=post["text_content"],
                    confidence_score=30, # STRICT LOW CONFIDENCE TAG
                    source_link=post["source_link"],
                    symptom=post.get("symptom"),
                    treatment=post.get("treatment"),
                    medication=post.get("medication"),
                    lifestyle_change=post.get("lifestyle_change"),
                    reported_outcome=post.get("reported_outcome"),
                    sentiment=post.get("sentiment"),
                )
                db.add(record)
                total_stored += 1
                print(f"  [+] Stored community report: {post['title'][:50]}...")
            else:
                print(f"  [-] Skipped (Duplicate): {post['title'][:40]}...")
        
        db.commit()
        print(f"Ingestion complete. Stored {total_stored} community reports.")
    finally:
        db.close()

if __name__ == "__main__":
    run_ingestion()
