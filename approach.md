# Healthcare Information Assistant - Technical Approach

## Overview

This is a Proof of Concept (POC) for a healthcare information assistant that provides verified, educational health information to users. It uses a Retrieval-Augmented Generation (RAG) architecture with strict source verification to ensure accuracy.

## Architecture

### RAG Pipeline

The system follows a standard RAG (Retrieval-Augmented Generation) pattern:

```
User Query
    |
    v
[1. Tavily Search] -- restricted to whitelisted medical domains
    |
    v
[2. Context Assembly] -- search results formatted with source labels
    |
    v
[3. Prompt Construction] -- system prompt + context + user query
    |
    v
[4. LLM (gpt-4o-mini)] -- generates response grounded in retrieved context
    |
    v
[5. Response + Source Citations] -- answer with inline citations + verified URLs
```

### Why RAG?

A pure LLM approach (without retrieval) would rely entirely on the model's training data, which may be outdated, incomplete, or hallucinated -- unacceptable for medical information. RAG grounds every response in real, freshly retrieved content from authoritative sources.

## Source Verification: Domain Whitelisting

The most critical design decision is **domain whitelisting via Tavily Search**.

### How It Works

The Tavily Search API accepts an `include_domains` parameter that restricts search results to only the specified domains. This is enforced server-side by Tavily, meaning the LLM only ever sees content from trusted sources.

### Whitelisted Domains

| Domain | Organization | Focus |
|--------|-------------|-------|
| mayoclinic.org | Mayo Clinic | General medicine |
| clevelandclinic.org | Cleveland Clinic | General medicine |
| hopkinsmedicine.org | Johns Hopkins Medicine | General medicine |
| cdc.gov | Centers for Disease Control | Public health |
| nih.gov | National Institutes of Health | Research-backed info |
| healthychildren.org | American Academy of Pediatrics | Pediatric / Family |
| kidshealth.org | Nemours Foundation | Pediatric / Family |
| nhs.uk | UK National Health Service | General medicine |
| who.int | World Health Organization | Global health |

All domains are from editorially reviewed, evidence-based medical institutions.

### Why Not Just Google Search?

General web search returns results from blogs, forums, and unverified sources. Domain whitelisting ensures that every piece of information in the response can be traced back to a trusted medical institution.

## Guardrails

### 1. System Prompt Constraints

The system prompt explicitly instructs the LLM to:
- Provide only informational and educational content
- Never provide diagnoses or treatment recommendations
- Never make predictions or assumptions
- Admit when insufficient verified information is available
- Recommend consulting a healthcare provider when appropriate
- Cite sources using [Source N] labels for verifiability

### 2. Temperature = 0

The LLM (gpt-4o-mini) is configured with `temperature=0`, which:
- Makes responses deterministic (same input = same output)
- Minimizes creative embellishment
- Reduces hallucination risk

### 3. Context-Only Responses

The prompt instructs the LLM to base its response ONLY on the provided context (retrieved search results), not on its parametric knowledge. If the context does not contain relevant information, the LLM is instructed to say so.

### 4. Source Citation

The response includes:
- **Inline citations**: The LLM references [Source N] labels within its answer
- **Verified source list**: Source URLs are displayed programmatically after the response, guaranteeing they match exactly what Tavily returned (not LLM-generated URLs)

## Data Flow (Detailed)

1. **User enters a health-related question** via the CLI
2. **Tavily Search API** is called with:
   - The user's query
   - `include_domains` set to 9 trusted medical domains
   - `max_results=5`
3. **Tavily returns** up to 5 search results, each containing:
   - `url`: The source page URL
   - `content`: Extracted text content from the page
4. **Results are formatted** into a numbered context string:
   - `[Source 1]: https://... \n Content: ...`
   - `[Source 2]: https://... \n Content: ...`
5. **The prompt is assembled** with: system prompt + formatted context + user query
6. **gpt-4o-mini processes** the prompt and generates a response that:
   - Answers the question using only the provided context
   - Includes inline [Source N] citations
7. **The response is displayed** to the user, followed by a programmatic list of all verified source URLs

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM | OpenAI gpt-4o-mini | Response generation |
| Search | Tavily Search API | Domain-restricted web search |
| Framework | LangChain | Prompt management, LLM integration |
| Config | python-dotenv | API key management |

## Limitations (POC Scope)

- **No conversation memory**: Each query is independent; the assistant does not remember previous questions
- **No persistent storage**: Search results and responses are not saved
- **CLI only**: No web interface; interaction is via command line
- **No authentication**: API keys are stored in .env file
- **English only**: No multi-language support
- **5 result limit**: Tavily returns max 5 results per query

## Setup

1. Set environment variables in `.env`:
   ```
   OPENAI_API_KEY=your-openai-api-key
   TAVILY_API_KEY=your-tavily-api-key
   ```
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python medical_assistant.py`
