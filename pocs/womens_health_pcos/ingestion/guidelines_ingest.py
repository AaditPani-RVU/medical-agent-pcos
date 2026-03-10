"""
Ingests high-confidence Clinical Guidelines for PCOS.
Stores extracted criteria and pathways into `treatment_protocols`.
For demonstration, this uses a pre-defined subset of major guidelines safely formatted.
"""

import sys
import os

# Add root project path to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from pocs.womens_health_pcos.database.session import SessionLocal, init_db
from pocs.womens_health_pcos.database.models import TreatmentProtocol

GUIDELINES = [
    {
        "title": "International Evidence-based Guideline for the Assessment and Management of PCOS 2023",
        "source_domain": "monash.edu",
        "source_link": "https://www.monash.edu/medicine/mchri/pcos/guideline",
        "diagnostic_criteria": "Rotterdam Criteria (2003) as endorsed by 2023 Guideline: Requires 2 of 3: 1) Oligo/anovulation, 2) Clinical or biochemical hyperandrogenism, 3) Polycystic ovaries on ultrasound (with exceptions for adolescents).",
        "symptom_requirements": "Irregular periods, hirsutism, severe acne, alopecia.",
        "hormone_thresholds": "Elevated free testosterone, FAI, or androstenedione. Exclude CAH, thyroid dysfunction, hyperprolactinemia.",
        "recommended_tests": "Total and free testosterone, SHBG, pelvic ultrasound (if >8 years post-menarche), OGTT for metabolic risk, lipid profile.",
        "treatment_pathways": "COCPs as first-line for cycle regulation/hyperandrogenism. Metformin for metabolic features. Letrozole as first-line for ovulation induction.",
        "lifestyle_recommendations": "Healthy eating principles, regular physical activity, target 5-10% weight loss if BMI>25, sleep hygiene, emotional wellbeing support.",
        "text_content": "The 2023 International Guideline provides comprehensive recommendations for diagnosis and management of Polycystic Ovary Syndrome...",
    },
    {
        "title": "Endocrine Society Clinical Practice Guideline on PCOS",
        "source_domain": "endocrine.org",
        "source_link": "https://www.endocrine.org/clinical-practice-guidelines/pcos",
        "diagnostic_criteria": "Recommend using the Rotterdam criteria for diagnosis of PCOS.",
        "symptom_requirements": "Focus on cutaneous manifestations of hyperandrogenism (hirsutism, acne).",
        "hormone_thresholds": "Calculated bioavailable or free testosterone is preferred.",
        "recommended_tests": "Screening for depression, anxiety, eating disorders, and obstructive sleep apnea.",
        "treatment_pathways": "Hormonal contraceptives for anovulation; Clomiphene or letrozole for infertility.",
        "lifestyle_recommendations": "Exercise therapy and balanced caloric intake reduction.",
        "text_content": "Endocrine Society guideline focusing on hormonal and metabolic derangements in PCOS patients...",
    }
]

def run_ingestion():
    init_db()
    print("Starting Clinical Guidelines Ingestion...")
    db = SessionLocal()
    total_stored = 0
    try:
        for gd in GUIDELINES:
            exists = db.query(TreatmentProtocol).filter(TreatmentProtocol.source_link == gd["source_link"]).first()
            if not exists:
                record = TreatmentProtocol(
                    title=gd["title"],
                    source_domain=gd["source_domain"],
                    text_content=gd["text_content"],
                    confidence_score=95, # Very high for guidelines
                    source_link=gd["source_link"],
                    diagnostic_criteria=gd.get("diagnostic_criteria"),
                    symptom_requirements=gd.get("symptom_requirements"),
                    hormone_thresholds=gd.get("hormone_thresholds"),
                    recommended_tests=gd.get("recommended_tests"),
                    treatment_pathways=gd.get("treatment_pathways"),
                    lifestyle_recommendations=gd.get("lifestyle_recommendations"),
                )
                db.add(record)
                total_stored += 1
                print(f"  [+] Stored guideline: {gd['title'][:60]}...")
            else:
                print(f"  [-] Skipped (Duplicate): {gd['title'][:40]}...")
        
        db.commit()
        print(f"Ingestion complete. Stored {total_stored} clinical guidelines.")
    finally:
        db.close()

if __name__ == "__main__":
    run_ingestion()
