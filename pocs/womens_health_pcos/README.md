# PCOS Knowledge Pipeline POC

Verified medical retrieval pipeline for aggregating, processing, and scoring healthcare knowledge focused on PCOS and women's health.

## Architecture

```
User Query
    ↓
Tavily Search (top 20, unrestricted)
    ↓
Deterministic Domain Filtering (ALLOWED_DOMAINS)
    ↓
Content Type Classification (ARTICLE / VIDEO)
    ↓
Confidence Scoring (HIGH / MEDIUM / LOW)
    ↓
Constraint Validation (dedup, length, quality)
    ↓
Content Extraction (LLM-assisted field extraction)
    ↓
Structured Knowledge Storage (PostgreSQL)
```

## Module Structure

```
pocs/womens_health_pcos/
├── retrieval/
│   ├── tavily_search.py          # Broad search wrapper
│   ├── domain_filter.py          # Strict allowlist filter
│   ├── content_classifier.py     # ARTICLE vs VIDEO
│   ├── confidence_scoring.py     # HIGH/MEDIUM/LOW tiers
│   └── constraints_validator.py  # Quality gate
├── extraction/
│   ├── article_extractor.py      # Structured article fields
│   └── youtube_extractor.py      # Video metadata + transcript
├── pipeline/
│   └── knowledge_ingestion.py    # Main orchestrator
├── schema/
│   ├── postgres_schema.sql       # 6 tables with indexes
│   └── models.py                 # Pydantic data models
├── configs/
├── data/
├── rules/
└── api/
```

## Trusted Domains

WHO · CDC · NIH · NHS · Mayo Clinic · Cleveland Clinic · Endocrine.org · PubMed · NCBI · Monash · ESHRE · ICMR · YouTube (filtered)

## Safety Constraints

- **Never diagnoses** medical conditions
- **Never recommends** medication
- Only provides **educational health information**
- All sources are **traceable** with confidence levels
- If no trusted sources found: returns explicit "No verified medical sources" message
