# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Healthcare Information Assistant — a RAG (Retrieval-Augmented Generation) POC that delivers verified, educational health information. Uses domain-whitelisted search (Tavily) + LLM-based source verification + strict guardrails to prevent hallucination in medical contexts.

## Commands

### Backend
```bash
# Install Python deps (use venv)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run backend server (FastAPI + Uvicorn, port 8000, auto-reload)
python server.py

# Run CLI-only mode (no web server)
python medical_assistant.py

# Quick test script for YouTube keyword extraction
python test_script.py
```

### Frontend
```bash
cd frontend

# Install
npm install

# Dev server (Vite)
npm run dev

# Production build (output: frontend/dist/, served by FastAPI)
npm run build

# Lint
npm run lint
```

### Full-stack dev
Run `python server.py` for the API, and `cd frontend && npm run dev` for hot-reloading frontend. The React app calls `http://localhost:8000/api/chat` directly (no Vite proxy configured).

For production: build frontend first (`npm run build`), then `python server.py` serves both API and static files from `frontend/dist/`.

## Architecture

### Backend (Python)

- **`server.py`** — FastAPI app with single endpoint `POST /api/chat`. Serves built frontend as static files. CORS is wide open (`*`) for dev.
- **`medical_assistant.py`** — Core RAG pipeline:
  1. **Tavily Search** — domain-whitelisted to 9 trusted medical sites (Mayo Clinic, CDC, NIH, etc.)
  2. **YouTube Search** — uses LangChain `YouTubeSearchTool` + keyword extraction via LLM
  3. **Shorts/Reels Search** — second Tavily instance searching `youtube.com` + `instagram.com`
  4. **Source Verification** — each retrieved result is verified for relevance/reliability by a separate LLM call (returns reliability score 1-100)
  5. **Response Generation** — `gpt-4o-mini` at temperature=0 with strict system prompt, inline `[Source N]` citations

Key objects: `tavily_search`, `shorts_tavily`, `youtube_search`, `llm` (all module-level singletons).

Main entry: `ask_health_assistant(query: str) -> dict` returns `{"response": str, "sources": [{"url", "score", "type"}]}`.

### Frontend (React + Vite + Tailwind v4)

- **`App.jsx`** — Chat state management, API calls via axios to `localhost:8000`
- **`components/Message.jsx`** — Renders chat bubbles with markdown-like formatting and source cards with reliability score bars. Exports `cn()` utility (clsx + twMerge).
- **`components/ChatInput.jsx`** — Textarea with Enter-to-submit, imports `cn` from Message.

### API Contract

```
POST /api/chat
Body: { "query": string }
Response: { "response": string, "sources": [{ "url": string, "score": int, "type": string }] }
```

## Environment Variables

Required in `.env` at project root:
- `OPENAI_API_KEY` — OpenAI API key (used for gpt-4o-mini)
- `TAVILY_API_KEY` — Tavily Search API key

## Key Constraints

- LLM responses must be grounded ONLY in retrieved context — never use parametric knowledge for medical claims
- All search results pass through LLM-based verification before inclusion
- The system prompt forbids diagnoses, treatment recommendations, and predictions
- Source URLs are passed through programmatically (never LLM-generated) to prevent URL hallucination
