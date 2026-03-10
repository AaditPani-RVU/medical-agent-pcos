import os
import sys

# Add root project path to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from pocs.womens_health_pcos.assessment.questionnaire import UserQuestionnaire
from pocs.womens_health_pcos.assessment.scoring_model import calculate_risk_score
from pocs.womens_health_pcos.assessment.pattern_engine import detect_patterns, generate_educational_queries
from medical_assistant import search_trusted_sources

def evaluate_pcos_patterns(user_data_dict: dict) -> dict:
    """
    Main evaluation workflow:
    1. Validates input via Pydantic model
    2. Runs scoring algorithm (LOW/MODERATE/HIGH)
    3. Runs pattern engine
    4. Fetches verified educational content mapped to those patterns
    5. Returns safe, non-diagnostic insights
    """
    
    # 1. Validate
    try:
        user_data = UserQuestionnaire(**user_data_dict)
    except Exception as e:
        return {"error": "Invalid input format.", "details": str(e)}

    # 2. Score
    risk_assessment = calculate_risk_score(user_data)
    
    # 3. Detect Patterns
    patterns = detect_patterns(user_data)
    
    # 4. Map to Content (Search verified DB)
    queries = generate_educational_queries(patterns)
    educational_content = []
    
    for query in queries[:2]: # Max 2 queries to prevent overloading Tavily/OpenAI
        print(f"[Content Mapper] Fetching verified knowledge for: {query}")
        # Re-use the existing trusted retrieval engine
        search_results = search_trusted_sources(query)
        if search_results and "context" in search_results:
            educational_content.append({
                "theme": query,
                "verified_sources": search_results["source_urls"],
                "content": search_results["context"]
            })

    # 5. Build final safe response
    response_text = f"## Pattern Assessment Summary\n"
    response_text += f"> {risk_assessment['recommendation']}\n\n"
    
    if patterns:
        formatted_patterns = [p.replace("_", " ").title() for p in patterns]
        response_text += f"**Detected Patterns:** {', '.join(formatted_patterns)}\n"
        response_text += "These are symptom clusters that are common in endocrine tracking. "
        response_text += "Your responses suggest patterns that are sometimes associated with hormonal imbalance.\n\n"
    
    response_text += f"**Contributing Factors:** {', '.join(risk_assessment['contributing_factors'])}\n"
    response_text += f"\n---\n*Disclaimer: {risk_assessment['safety_disclaimer']}*\n---\n"
    
    return {
        "assessment": risk_assessment,
        "patterns_detected": patterns,
        "educational_payload": educational_content,
        "display_text": response_text
    }
