"""
Ingests Population Health and Demographic data regarding PCOS.
Stores extracted patterns into `demographic_patterns`.
Uses predefined structured data representing WHO/ICMR statistics.
"""

import sys
import os

# Add root project path to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from pocs.womens_health_pcos.database.session import SessionLocal, init_db
from pocs.womens_health_pcos.database.models import DemographicPattern

POPULATION_DATA = [
    {
        "title": "Global Prevalence of PCOS (WHO Estimates)",
        "source_domain": "who.int",
        "source_link": "https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome",
        "age_distribution": "Reproductive age (15-49 years)",
        "urban_vs_rural_patterns": "Higher reported rates in urban populations linked to lifestyle factors.",
        "lifestyle_factors": "Sedentary behaviors and ultra-processed diets strongly correlate with phenotypic severity.",
        "comorbidities": "Type 2 Diabetes (up to 40% before age 40), gestational diabetes, cardiovascular disease risk, depression.",
        "prevalence_rates": "Affects an estimated 8-13% of women of reproductive age. Up to 70% remain undiagnosed worldwide.",
        "text_content": "PCOS is a common hormonal condition that affects women of reproductive age. It usually starts during adolescence. Symptoms include...",
    },
    {
        "title": "PCOS Prevalence and Patterns in India (ICMR/NFHS Reports Overview)",
        "source_domain": "icmr.nic.in",
        "source_link": "https://www.icmr.nic.in/pcos_overview", # Example URL
        "age_distribution": "18-40 years, with rising detection in adolescent girls 15-18 years.",
        "urban_vs_rural_patterns": "Significantly higher prevalence in urban centers (approx. 9-11%) compared to rural areas (3-5%).",
        "lifestyle_factors": "Dietary shifts toward high-glycemic index foods and reduced physical activity in urban centers.",
        "comorbidities": "Insulin resistance (pre-diabetes), hypothyroidism, metabolic syndrome, and clinical depression.",
        "prevalence_rates": "Estimated 9.13% overall pooled prevalence in Indian women of reproductive age.",
        "text_content": "A systemic review of PCOS in India shows a rising trend directly correlating with urbanization and lifestyle changes...",
    }
]

def run_ingestion():
    init_db()
    print("Starting Population Health Ingestion...")
    db = SessionLocal()
    total_stored = 0
    try:
        for pdata in POPULATION_DATA:
            exists = db.query(DemographicPattern).filter(DemographicPattern.source_link == pdata["source_link"]).first()
            if not exists:
                record = DemographicPattern(
                    title=pdata["title"],
                    source_domain=pdata["source_domain"],
                    text_content=pdata["text_content"],
                    confidence_score=90, # High confidence for epidemiologic data
                    source_link=pdata["source_link"],
                    age_distribution=pdata.get("age_distribution"),
                    urban_vs_rural_patterns=pdata.get("urban_vs_rural_patterns"),
                    lifestyle_factors=pdata.get("lifestyle_factors"),
                    comorbidities=pdata.get("comorbidities"),
                    prevalence_rates=pdata.get("prevalence_rates"),
                )
                db.add(record)
                total_stored += 1
                print(f"  [+] Stored population data: {pdata['title'][:50]}...")
            else:
                print(f"  [-] Skipped (Duplicate): {pdata['title'][:40]}...")
        
        db.commit()
        print(f"Ingestion complete. Stored {total_stored} demographic patterns.")
    finally:
        db.close()

if __name__ == "__main__":
    run_ingestion()
