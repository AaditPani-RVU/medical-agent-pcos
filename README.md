# Healthcare Information Assistant

A Proof of Concept (POC) Retrieval-Augmented Generation (RAG) assistant for delivering verified, educational health information to users.

This prototype focuses on **source verification** and **strict guardrails**, addressing the hallucination and unreliability risks associated with using pure LLMs for medical inquiries.

## Features

- **Domain Whitelisting**: Searches are restricted server-side via Tavily Search to trusted medical institutions (e.g., Mayo Clinic, NIH, CDC, WHO). The LLM never sees unverified content.
- **Strict System Prompting**: Prevents the assistant from generating diagnoses, medical advice, or predictions.
- **Zero Temperature**: Responses operate with `temperature=0` to ensure determinism and minimize creative embellishment or hallucinations.
- **Contextual Grounding**: The LLM is forced to answer _only_ using retrieved context. It is designed to decline answers if verified information is unavailable.
- **Transparent Citations**: Responses include inline `[Source N]` citations, paired with a programmatic list of exact source URLs.
- **Video Sources**: YouTube videos, Shorts, and Instagram Reels are searched and embedded alongside article sources, with reliability scoring.
- **Prescription OCR**: Upload a prescription image and the system extracts medications, dosages, and conditions using Google Gemini Vision, then runs the full RAG pipeline on the extracted information.
- **Web UI**: React + Vite + Tailwind frontend with chat interface, source cards, embedded video players, and prescription upload.

## Whitelisted Domains

Currently, the search engine is strictly limited to:

- `mayoclinic.org`
- `clevelandclinic.org`
- `hopkinsmedicine.org`
- `cdc.gov`
- `nih.gov`
- `healthychildren.org`
- `kidshealth.org`
- `nhs.uk`
- `who.int`

## Architecture

1. **User Query**: User inputs a health query via the web UI (or uploads a prescription image).
2. **Prescription OCR** (optional): If an image is uploaded, Google Gemini Vision extracts medications, dosages, and conditions.
3. **Search (Tavily + YouTube)**: Searches whitelisted medical domains (articles), YouTube (videos), and YouTube/Instagram (shorts/reels).
4. **Source Verification**: Each result is verified for relevance and reliability by a separate LLM call with a reliability score (1-100).
5. **Prompt Assembly**: Combines the strict system prompt, verified documents (as context), and the user's query.
6. **Generation (Google Gemini gemini-2.5-flash)**: Generates an answer strictly grounded in the provided context, along with citations.
7. **Output**: Displays the response with inline citations, source cards with reliability scores, and embedded video players.

## Setup Instructions

### Prerequisites

- Python 3.8+
- A Google Gemini API Key
- A Tavily API Key

### Installation

1. **Clone the repository** (if applicable) and navigate to the project directory:

   ```bash
   cd NewPoc
   ```

2. **Set up environment variables**:
   Create a `.env` file in the root directory and add your API keys:

   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

**Backend:**
```bash
python server.py
```

**Frontend (dev mode):**
```bash
cd frontend && npm install && npm run dev
```

**Production:** Build the frontend first (`cd frontend && npm run build`), then `python server.py` serves both the API and static files at `http://localhost:8000`.

**CLI only (no web server):**
```bash
python medical_assistant.py
```

## Tech Stack

- **LLM**: Google `gemini-2.5-flash` (chat, verification, and prescription OCR)
- **Search**: Tavily Search API (articles + shorts/reels), LangChain YouTubeSearchTool
- **Backend**: FastAPI + Uvicorn
- **Frontend**: React + Vite + Tailwind CSS v4 + Framer Motion
- **Framework**: LangChain
- **Configuration**: Python `dotenv`

## Limitations (POC Scope)

- **No Persistence**: Chat logs and retrieved documents are not saved across sessions.
- **English Focus**: Multi-language support is not currently implemented.
- **Prescription OCR**: Accuracy depends on handwriting legibility; best with printed or clearly written prescriptions.
