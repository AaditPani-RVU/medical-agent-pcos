-- Verified Medical Retrieval Pipeline — PostgreSQL Schema
-- Supports PCOS knowledge base with article + video content types

-- Core table for all retrieved sources
CREATE TABLE IF NOT EXISTS research_sources (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source_url TEXT UNIQUE NOT NULL,
    source_domain TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN ('ARTICLE', 'VIDEO')),
    confidence_level TEXT NOT NULL CHECK (confidence_level IN ('HIGH', 'MEDIUM', 'LOW_VIDEO_CONFIDENCE')),
    confidence_score INTEGER CHECK (confidence_score BETWEEN 0 AND 100),
    query_topic TEXT,
    raw_content TEXT,
    extracted_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Symptom patterns extracted from sources
CREATE TABLE IF NOT EXISTS symptom_patterns (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES research_sources(id) ON DELETE CASCADE,
    symptom_name TEXT NOT NULL,
    prevalence TEXT,
    severity TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lab markers referenced in sources
CREATE TABLE IF NOT EXISTS lab_markers (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES research_sources(id) ON DELETE CASCADE,
    marker_name TEXT NOT NULL,
    normal_range TEXT,
    pcos_range TEXT,
    significance TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Treatment protocols
CREATE TABLE IF NOT EXISTS treatment_protocols (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES research_sources(id) ON DELETE CASCADE,
    treatment_name TEXT NOT NULL,
    treatment_type TEXT, -- 'medication', 'lifestyle', 'surgical', 'supplement'
    evidence_level TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Demographic patterns
CREATE TABLE IF NOT EXISTS demographic_patterns (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES research_sources(id) ON DELETE CASCADE,
    population TEXT,
    age_group TEXT,
    prevalence_rate TEXT,
    region TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Community reports and patient experience data
CREATE TABLE IF NOT EXISTS community_reports (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES research_sources(id) ON DELETE CASCADE,
    report_type TEXT, -- 'experience', 'survey', 'case_study'
    summary TEXT,
    sentiment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sources_topic ON research_sources(query_topic);
CREATE INDEX IF NOT EXISTS idx_sources_type ON research_sources(content_type);
CREATE INDEX IF NOT EXISTS idx_sources_confidence ON research_sources(confidence_level);
CREATE INDEX IF NOT EXISTS idx_symptoms_name ON symptom_patterns(symptom_name);
CREATE INDEX IF NOT EXISTS idx_lab_markers_name ON lab_markers(marker_name);
