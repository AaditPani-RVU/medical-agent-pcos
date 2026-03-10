"""
Ingests PCOS research papers from PubMed via NCBI E-utilities.
Stores the extracted metadata into the `research_sources` table.
"""

import sys
import os
import time

# Add root project path to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from pocs.womens_health_pcos.database.session import SessionLocal, init_db
from pocs.womens_health_pcos.database.models import ResearchSource

try:
    from Bio import Entrez
except ImportError:
    print("Biopython not installed. Please pip install biopython")
    sys.exit(1)

Entrez.email = "dory_bot@example.com"  # Always provide an email to NCBI

QUERIES = [
    "PCOS prevalence OR polycystic ovary syndrome prevalence",
    "PCOS insulin resistance",
    "PCOS symptoms diagnosis",
    "PCOS treatment OR polycystic ovary syndrome treatment",
    "PCOS lifestyle intervention",
    "PCOS fertility outcomes"
]

def search_pubmed(query, max_results=5):
    """Search PubMed and return a list of PMIDs."""
    print(f"Searching PubMed for: '{query}'")
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="relevance")
        record = Entrez.read(handle)
        handle.close()
        return record["IdList"]
    except Exception as e:
        print(f"Error searching PubMed: {e}")
        return []

def fetch_paper_details(pmid):
    """Fetch details for a given PMID and extract relevant medical fields."""
    try:
        handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        
        article = records['PubmedArticle'][0]['MedlineCitation']['Article']
        
        title = article.get('ArticleTitle', '')
        
        # Extract abstract
        abstract = ""
        if 'Abstract' in article and 'AbstractText' in article['Abstract']:
            abstract_texts = article['Abstract']['AbstractText']
            # Sometimes abstract is a list of sections (Background, Methods, etc.)
            for text in abstract_texts:
                label = text.attributes.get('Label', '')
                if label:
                    abstract += f"{label}: {str(text)}\n"
                else:
                    abstract += f"{str(text)}\n"
                    
        # Extract Year
        year = None
        if 'Journal' in article and 'JournalIssue' in article['Journal']:
            pub_date = article['Journal']['JournalIssue'].get('PubDate', {})
            year = pub_date.get('Year')
            
        return {
            "title": title,
            "abstract": abstract.strip(),
            "year": int(year) if year and year.isdigit() else None,
            "pmid": pmid
        }
    except Exception as e:
        print(f"Error fetching details for PMID {pmid}: {e}")
        return None

def store_research(paper):
    """Store paper metadata into the ResearchSource table."""
    db = SessionLocal()
    try:
        # Check if exists
        source_link = f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/"
        exists = db.query(ResearchSource).filter(ResearchSource.source_link == source_link).first()
        if exists:
            return False
            
        # Basic parsing heuristics for structured fields
        abstract_lower = paper['abstract'].lower()
        
        # Very simple mocked extraction for demonstration (in production, use LLM or strict regex)
        symptoms = []
        if "acne" in abstract_lower: symptoms.append("acne")
        if "hirsutism" in abstract_lower: symptoms.append("hirsutism")
        if "irregular" in abstract_lower or "oligo" in abstract_lower: symptoms.append("irregular cycles")
        if "weight" in abstract_lower or "obesity" in abstract_lower: symptoms.append("weight gain")
        
        record = ResearchSource(
            title=paper['title'],
            source_domain="pubmed.ncbi.nlm.nih.gov",
            content_type="RESEARCH_ARTICLE",
            text_content=paper['abstract'][:5000],  # Cap abstract
            confidence_score=70,  # Medium confidence for general peer-reviewed
            source_link=source_link,
            year=paper['year'],
            symptoms_identified=", ".join(symptoms) if symptoms else None,
            key_conclusions=paper['abstract'][:1000] # Use first block as conclusion proxy
        )
        
        db.add(record)
        db.commit()
        return True
    finally:
        db.close()

def run_ingestion():
    init_db()  # Ensure tables exist
    print("Starting PubMed Ingestion Pipeline...")
    total_stored = 0
    
    for query in QUERIES:
        pmids = search_pubmed(query, max_results=3) # Small limit for demo
        for pmid in pmids:
            paper = fetch_paper_details(pmid)
            if paper and paper['abstract']:
                if store_research(paper):
                    print(f"  [+] Stored: {paper['title'][:60]}...")
                    total_stored += 1
                else:
                    print(f"  [-] Skipped (Duplicate): {paper['title'][:40]}...")
            time.sleep(0.5) # Rate limit respect
            
    print(f"Ingestion complete. Stored {total_stored} new research papers.")

if __name__ == "__main__":
    run_ingestion()
