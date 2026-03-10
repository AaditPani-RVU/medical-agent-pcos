from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from pocs.womens_health_pcos.database.base import Base

class ResearchSource(Base):
    """Stores PubMed and other research papers."""
    __tablename__ = "research_sources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_domain = Column(String, nullable=False)
    content_type = Column(String, default="ARTICLE")
    text_content = Column(Text, nullable=False)
    confidence_score = Column(Integer, default=70) # Medium confidence
    source_link = Column(String, unique=True, nullable=False)
    date_added = Column(DateTime(timezone=True), server_default=func.now())
    
    # Paper-specific metadata
    year = Column(Integer, nullable=True)
    study_population = Column(String, nullable=True)
    sample_size = Column(Integer, nullable=True)
    age_group = Column(String, nullable=True)
    symptoms_identified = Column(String, nullable=True)
    lab_markers = Column(String, nullable=True)
    treatment_protocol = Column(String, nullable=True)
    outcomes = Column(String, nullable=True)
    key_conclusions = Column(Text, nullable=True)


class SymptomPattern(Base):
    """Stores symptom relationships and cluster definitions."""
    __tablename__ = "symptom_patterns"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_domain = Column(String, nullable=False)
    content_type = Column(String, default="PATTERN")
    text_content = Column(Text, nullable=False)
    confidence_score = Column(Integer, nullable=False)
    source_link = Column(String, nullable=True)
    date_added = Column(DateTime(timezone=True), server_default=func.now())
    
    pattern_cluster = Column(String, nullable=False) # e.g. insulin_resistance
    associated_symptoms = Column(String, nullable=False)


class LabMarker(Base):
    """Stores information about relevant lab tests and thresholds."""
    __tablename__ = "lab_markers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_domain = Column(String, nullable=False)
    content_type = Column(String, default="LAB_GUIDE")
    text_content = Column(Text, nullable=False)
    confidence_score = Column(Integer, nullable=False)
    source_link = Column(String, nullable=True)
    date_added = Column(DateTime(timezone=True), server_default=func.now())
    
    marker_name = Column(String, nullable=False)
    normal_range = Column(String, nullable=True)
    pcos_pattern = Column(String, nullable=True)


class TreatmentProtocol(Base):
    """Stores clinical guidelines for treatments and lifestyle changes."""
    __tablename__ = "treatment_protocols"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_domain = Column(String, nullable=False)
    content_type = Column(String, default="GUIDELINE")
    text_content = Column(Text, nullable=False)
    confidence_score = Column(Integer, default=90) # High confidence
    source_link = Column(String, unique=True, nullable=False)
    date_added = Column(DateTime(timezone=True), server_default=func.now())
    
    diagnostic_criteria = Column(Text, nullable=True)
    symptom_requirements = Column(Text, nullable=True)
    hormone_thresholds = Column(Text, nullable=True)
    recommended_tests = Column(Text, nullable=True)
    treatment_pathways = Column(Text, nullable=True)
    lifestyle_recommendations = Column(Text, nullable=True)


class DemographicPattern(Base):
    """Stores population health data (WHO, ICMR, etc.)."""
    __tablename__ = "demographic_patterns"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_domain = Column(String, nullable=False)
    content_type = Column(String, default="POPULATION_DATA")
    text_content = Column(Text, nullable=False)
    confidence_score = Column(Integer, default=90)
    source_link = Column(String, nullable=False)
    date_added = Column(DateTime(timezone=True), server_default=func.now())
    
    age_distribution = Column(String, nullable=True)
    urban_vs_rural_patterns = Column(String, nullable=True)
    lifestyle_factors = Column(String, nullable=True)
    comorbidities = Column(String, nullable=True)
    prevalence_rates = Column(String, nullable=True)


class CommunityReport(Base):
    """Stores anecdotal community experiences (Reddit, Quora, etc.)."""
    __tablename__ = "community_reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_domain = Column(String, nullable=False)
    content_type = Column(String, default="ANECDOTAL")
    text_content = Column(Text, nullable=False)
    confidence_score = Column(Integer, default=30) # LOW confidence
    source_link = Column(String, unique=True, nullable=False)
    date_added = Column(DateTime(timezone=True), server_default=func.now())
    
    symptom = Column(String, nullable=True)
    treatment = Column(String, nullable=True)
    medication = Column(String, nullable=True)
    lifestyle_change = Column(String, nullable=True)
    reported_outcome = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)
