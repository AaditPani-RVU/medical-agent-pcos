from pydantic import BaseModel, conint, Field
from typing import List, Optional

class UserQuestionnaire(BaseModel):
    """
    Pydantic model representing the user's input for the PCOS evaluation.
    Collects demographic, symptom, and lifestyle data.
    """
    # Demographics & Body Metrics
    age: conint(ge=10, le=99) = Field(..., description="User's age in years")
    height_cm: Optional[float] = Field(None, description="Height in centimeters")
    weight_kg: Optional[float] = Field(None, description="Weight in kilograms")
    
    # Cycles
    cycle_regularity: str = Field(..., description="Options: 'regular', 'irregular', 'absent'")
    cycle_length_days: Optional[int] = Field(None, description="Average length of cycle in days")
    
    # Symptoms
    symptoms: List[str] = Field(
        default_factory=list,
        description="List of experienced symptoms (e.g. 'acne', 'hirsutism', 'hair_loss', 'weight_gain', 'fatigue')"
    )
    
    # Lifestyle
    energy_levels: str = Field(..., description="Options: 'high', 'normal', 'low', 'exhausted'")
    
    # History
    family_history_pcos: bool = Field(False, description="Does an immediate family member have PCOS?")
    family_history_diabetes: bool = Field(False, description="Does an immediate family member have Type 2 Diabetes?")
    
    # Primary Concern
    primary_health_concern: Optional[str] = Field(None, description="Main reason for taking the questionnaire")

    @property
    def bmi(self) -> Optional[float]:
        """Calculate BMI if height and weight are provided."""
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None
