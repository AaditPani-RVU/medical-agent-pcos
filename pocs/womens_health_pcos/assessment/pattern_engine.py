from pocs.womens_health_pcos.assessment.questionnaire import UserQuestionnaire

def detect_patterns(user_data: UserQuestionnaire) -> list[str]:
    """
    Rule-based pattern detection system.
    Identifies underlying physiological patterns based on reported symptoms.
    Does NOT diagnose. Identifies "patterns".
    """
    patterns = []
    symptoms = [s.lower() for s in user_data.symptoms]
    
    # 1. Hormonal Imbalance Pattern (Androgen excess + cycle issues)
    has_hyperandrogenism = any(s in symptoms for s in ["acne", "hirsutism", "hair_loss"])
    has_cycle_issue = user_data.cycle_regularity in ["irregular", "absent"]
    if has_hyperandrogenism and has_cycle_issue:
        patterns.append("hormonal_imbalance")

    # 2. Insulin Resistance Pattern (Weight, fatigue, family history)
    has_metabolic_symptoms = "weight_gain" in symptoms or user_data.energy_levels in ["low", "exhausted"]
    has_diabetes_risk = user_data.family_history_diabetes or (user_data.bmi and user_data.bmi >= 25.0)
    if has_metabolic_symptoms and has_diabetes_risk:
        patterns.append("insulin_resistance_pattern")

    # 3. Reproductive Irregularity Pattern (Cycles without distinct hyperandrogenism necessarily)
    if has_cycle_issue and not has_hyperandrogenism:
        patterns.append("reproductive_irregularity")
        
    # 4. General Metabolic Risk
    if user_data.bmi and user_data.bmi > 30.0:
        patterns.append("metabolic_risk")
        
    return patterns

def generate_educational_queries(patterns: list[str]) -> list[str]:
    """Maps detected patterns to standard search queries for the Retrieval Engine."""
    queries = []
    for p in patterns:
        if p == "hormonal_imbalance":
            queries.append("PCOS hormonal imbalance symptoms and lifestyle management")
        elif p == "insulin_resistance_pattern":
            queries.append("PCOS insulin resistance weight gain and dietary treatment")
        elif p == "reproductive_irregularity":
            queries.append("PCOS irregular cycles anovulation causes")
        elif p == "metabolic_risk":
            queries.append("PCOS metabolic syndrome risk factors and exercise")
            
    # Default fallback if no patterns detected
    if not queries:
        queries.append("PCOS general health guidelines and cycle tracking")
        
    return queries
