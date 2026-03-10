from pocs.womens_health_pcos.assessment.questionnaire import UserQuestionnaire

def calculate_risk_score(user_data: UserQuestionnaire) -> dict:
    """
    Calculates a risk awareness score based on questionnaire inputs.
    
    Score Components:
    - symptom_score: +2 for major symptoms (irregular cycles, hirsutism, acne)
    - lifestyle_score: +1 for low energy or high BMI
    - family_history_score: +2 for PCOS/Diabetes family history
    - age_factor: +1 if typical onset age (15-30)
    
    Total Score determines Category:
    - 0-2: LOW (awareness)
    - 3-5: MODERATE (monitoring recommended)
    - 6+: HIGH (pattern awareness, consult doctor)
    """
    
    score = 0
    factors = []
    
    # Symptom Score
    if user_data.cycle_regularity in ['irregular', 'absent']:
        score += 2
        factors.append("Irregular or absent menstrual cycles")
        
    major_symptoms = ["hirsutism", "acne", "hair_loss", "weight_gain"]
    matched_symptoms = [s for s in user_data.symptoms if s.lower() in major_symptoms]
    if matched_symptoms:
        score += len(matched_symptoms)
        factors.append(f"Physical symptoms ({', '.join(matched_symptoms)})")

    # Lifestyle Score
    if user_data.energy_levels in ['low', 'exhausted']:
        score += 1
        factors.append("Chronic low energy/fatigue")
        
    bmi = user_data.bmi
    if bmi and bmi >= 25.0:
        score += 1
        factors.append(f"Elevated BMI ({bmi})")
        
    # Family History Score
    if user_data.family_history_pcos:
        score += 2
        factors.append("Family history of PCOS")
    if user_data.family_history_diabetes:
        score += 1
        factors.append("Family history of Type 2 Diabetes")
        
    # Age Factor
    if 15 <= user_data.age <= 30:
        score += 1
        
    # Determine Category
    if score >= 6:
        category = "HIGH"
        recommendation = "High pattern awareness. We strongly encourage consulting a healthcare professional for a formal evaluation."
    elif score >= 3:
        category = "MODERATE"
        recommendation = "Moderate monitoring recommended. These patterns are worth discussing with a doctor at your next visit."
    else:
        category = "LOW"
        recommendation = "Low awareness. Focus on general wellness and track your cycles."

    return {
        "total_score": score,
        "category": category,
        "contributing_factors": factors,
        "recommendation": recommendation,
        "safety_disclaimer": "This score is for educational pattern awareness only and is NOT a medical diagnosis."
    }
