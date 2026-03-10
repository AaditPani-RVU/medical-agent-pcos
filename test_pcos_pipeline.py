import os
import sys

# Add root project path to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pocs.womens_health_pcos.database.session import init_db
from pocs.womens_health_pcos.ingestion import guidelines_ingest, population_ingest, community_ingest
from medical_assistant import evaluate_pcos
import json

def test_pipeline():
    print("--- 1. Initializing DB ---")
    init_db()
    
    print("\n--- 2. Running Fast Ingestions ---")
    guidelines_ingest.run_ingestion()
    population_ingest.run_ingestion()
    community_ingest.run_ingestion()
    print("\n(Skipping PubMed ingest in test to prevent E-Utilities rate limits hanging)")

    print("\n--- 3. Testing evaluate_pcos endpoint ---")
    mock_input = {
        "age": 28,
        "height_cm": 165,
        "weight_kg": 85,
        "cycle_regularity": "irregular",
        "symptoms": ["acne", "fatigue", "weight_gain"],
        "energy_levels": "low",
        "family_history_diabetes": True
    }
    
    print(f"User Input: {mock_input}")
    result = evaluate_pcos(mock_input)
    
    print("\n--- RESULTS ---")
    print(json.dumps(result, indent=2))
    print("----------------")

if __name__ == "__main__":
    test_pipeline()
