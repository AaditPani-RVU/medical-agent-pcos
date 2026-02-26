# Healthcare Information Assistant

A Proof of Concept (POC) Retrieval-Augmented Generation (RAG) assistant for delivering verified, educational health information to users.

This prototype focuses on **source verification** and **strict guardrails**, addressing the hallucination and unreliability risks associated with using pure LLMs for medical inquiries.

## Features

- **Domain Whitelisting**: Searches are restricted server-side via Tavily Search to trusted medical institutions (e.g., Mayo Clinic, NIH, CDC, WHO). The LLM never sees unverified content.
- **Strict System Prompting**: Prevents the assistant from generating diagnoses, medical advice, or predictions.
- **Zero Temperature**: Responses operate with `temperature=0` to ensure determinism and minimize creative embellishment or hallucinations.
- **Contextual Grounding**: The LLM is forced to answer _only_ using retrieved context. It is designed to decline answers if verified information is unavailable.
- **Transparent Citations**: Responses include inline `[Source N]` citations, paired with a programmatic list of exact source URLs.

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

1. **User Query**: User inputs a health query via the CLI.
2. **Search (Tavily)**: Interrogates only the whitelisted domains and retrieves top 5 verified documents.
3. **Prompt Assembly**: Combines the strict system prompt, retrieved documents (as context), and the user's query.
4. **Generation (OpenAI gpt-4o-mini)**: Generates an answer strictly grounded in the provided context, along with citations.
5. **Output**: Displays the assistant's response accompanied by clickable URLs verifying the source.

## Setup Instructions

### Prerequisites

- Python 3.8+
- An OpenAI API Key
- A Tavily API Key

### Installation

1. **Clone the repository** (if applicable) and navigate to the project directory:

   ```bash
   cd NewPoc
   ```

2. **Set up environment variables**:
   Create a `.env` file in the root directory and add your API keys:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Execute the Python script to start the interactive CLI assistant:

```bash
python medical_assistant.py
```

Type your health-related questions. Type `exit` or `quit` to stop the assistant.

## Tech Stack

- **LLM**: OpenAI `gpt-4o-mini`
- **Search Provider**: Tavily Search API
- **Framework**: LangChain
- **Configuration**: Python `dotenv`

## Limitations (POC Scope)

- **No Memory**: Each interaction is stateless; the assistant does not recall previous questions.
- **CLI Only**: Does not yet have a web or graphical user interface.
- **No Persistence**: Chat logs and retrieved documents are not saved.
- **English Focus**: Multi-language support is not currently implemented.
