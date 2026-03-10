# Healthcare Information Assistant - Technical Approach

## Overview

This is a Proof of Concept (POC) for a healthcare information assistant that provides verified, educational health information to users. It uses a Retrieval-Augmented Generation (RAG) architecture with strict source verification to ensure accuracy.

## Architecture

### RAG Pipeline

The system follows an extended RAG (Retrieval-Augmented Generation) pattern:

```
User Query / Prescription Image
    |
    v
[0. Prescription OCR (optional)] -- gemini-2.5-flash extracts meds, dosages, conditions
    |
    v
[1a. Tavily Search] -- restricted to whitelisted medical domains (articles)
[1b. YouTube Search] -- LangChain YouTubeSearchTool for video content
[1c. Shorts/Reels Search] -- Tavily searching youtube.com + instagram.com
    |
    v
[2. Source Verification] -- each result scored by LLM for relevance/reliability (1-100)
    |
    v
[3. Context Assembly] -- verified results formatted with source labels
    |
    v
[4. Prompt Construction] -- system prompt + context + user query
    |
    v
[5. LLM (gemini-2.5-flash)] -- generates response grounded in retrieved context
    |
    v
[6. Response + Source Citations] -- answer with inline citations, source cards, embedded videos
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

The LLM (gemini-2.5-flash) is configured with `temperature=0`, which:
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

1. **User enters a health-related question** via the web UI, or **uploads a prescription image**
2. **If prescription uploaded**: Google Gemini Vision (gemini-2.5-flash) extracts medications, dosages, frequency, and conditions from the image. The extracted text is auto-sent as a chat message.
3. **Query contextualization**: If there is chat history, the query is rewritten into a standalone search query using the LLM.
4. **Three parallel searches** are performed:
   - **Tavily Search** (whitelisted medical domains, max 5 results)
   - **YouTube Search** (LangChain YouTubeSearchTool, 3 results using extracted keywords)
   - **Shorts/Reels Search** (Tavily on youtube.com + instagram.com, max 5 results)
5. **Source verification**: Each result is individually verified by the LLM for relevance and reliability, producing a score (1-100). Articles require `is_reliable: true`; video sources use a lower threshold (score >= 30) since their text content is often minimal.
6. **Context assembly**: Verified results are formatted with source labels and scores.
7. **gemini-2.5-flash processes** the prompt and generates a response grounded only in the provided context, with inline [Source N] citations.
8. **The response is displayed** in the web UI with source cards (reliability score bars), embedded YouTube/Instagram players, and fallback link pills for non-embeddable URLs.

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM (Chat) | Google gemini-2.5-flash | Response generation, verification, keyword extraction |
| LLM (Vision) | Google gemini-2.5-flash | Prescription OCR |
| Article Search | Tavily Search API | Domain-restricted medical web search |
| Video Search | LangChain YouTubeSearchTool | YouTube video discovery |
| Shorts/Reels Search | Tavily Search API | YouTube Shorts + Instagram Reels |
| Backend | FastAPI + Uvicorn | REST API server |
| Frontend | React + Vite + Tailwind v4 | Chat UI with embedded media |
| Framework | LangChain | Prompt management, LLM integration |
| Config | python-dotenv | API key management |

## Limitations (POC Scope)

- **No persistent storage**: Search results and responses are not saved across sessions
- **No authentication**: API keys are stored in .env file
- **English only**: No multi-language support
- **Prescription OCR**: Accuracy depends on handwriting legibility

## Setup

1. Set environment variables in `.env`:
   ```
   GEMINI_API_KEY=your-gemini-api-key
   TAVILY_API_KEY=your-tavily-api-key
   ```
2. Install dependencies: `pip install -r requirements.txt`
3. Build frontend: `cd frontend && npm install && npm run build`
4. Run: `python server.py`
