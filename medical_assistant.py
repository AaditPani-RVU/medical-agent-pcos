import os
import json
import ast
import asyncio
import base64
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.tools import YouTubeSearchTool
from openai import AsyncOpenAI

# Load environment variables (API keys)
load_dotenv()

# Ensure API keys are set
if not os.getenv("OPENAI_API_KEY"):
    print("WARNING: OPENAI_API_KEY environment variable is not set.")
if not os.getenv("TAVILY_API_KEY"):
    print("WARNING: TAVILY_API_KEY environment variable is not set.")

# --- 1. Define Trusted Sources ---
# This is the "Whitelist" that ensures we only search verified domains
ALLOWED_DOMAINS = [
    "who.int",
    "cdc.gov",
    "nih.gov",
    "nhs.uk",
    "mayoclinic.org",
    "clevelandclinic.org",
    "endocrine.org",
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "monash.edu",
    "eshre.eu"
]

HIGH_CONFIDENCE_DOMAINS = [
    "who.int", "cdc.gov", "nih.gov", "nhs.uk", 
    "mayoclinic.org", "clevelandclinic.org", "endocrine.org", "eshre.eu"
]

MEDIUM_CONFIDENCE_DOMAINS = [
    "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "monash.edu"
]

def get_domain_from_url(url: str) -> str:
    """Extracts the base domain from a URL for strict allowlist matching."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

def get_confidence_score(url: str) -> tuple:
    """Returns (label, base_score) for a domain."""
    domain = get_domain_from_url(url)
    if any(domain == d or domain.endswith("." + d) for d in HIGH_CONFIDENCE_DOMAINS):
        return "HIGH", 90
    if any(domain == d or domain.endswith("." + d) for d in MEDIUM_CONFIDENCE_DOMAINS):
        return "MEDIUM", 70
    return "LOW", 0

# --- 2. Initialize Search Tool ---
# We configure Tavily to specifically search ONLY the included domains.
# We fetch max 5 results to give the LLM enough context without overwhelming it.
tavily_search = TavilySearch(
    max_results=20
)

# --- 2b. Initialize Social Search Tools ---
youtube_search = YouTubeSearchTool()

SOCIAL_DOMAINS = ["youtube.com", "instagram.com"]
shorts_tavily = TavilySearch(
    max_results=5
)

# --- Local Medical Dictionaries for Prescription Pipeline ---
medical_terms_db = {
    "tsh": "Thyroid Stimulating Hormone, a hormone used to evaluate thyroid function.",
    "irregular menstrual cycle": "A menstrual cycle that does not occur at regular intervals.",
    "ultrasound": "A medical imaging technique used to examine internal organs.",
    "u/s": "Ultrasound, a medical imaging technique used to examine internal organs.",
    "pcos": "Polycystic Ovary Syndrome, a hormonal disorder.",
    "lh": "Luteinizing Hormone, a hormone associated with reproduction.",
    "fsh": "Follicle-Stimulating Hormone, a hormone associated with reproduction."
}

medicine_db = {
    "mif": "A medication sometimes prescribed in reproductive health contexts or vitamin supplementation (Myo-inositol / D-Chiro Inositol).",
    "metformin": "A medication often used to treat type 2 diabetes and insulin resistance in PCOS.",
    "letrozole": "A medication used to induce ovulation.",
    "clomid": "A medication used to induce ovulation.",
    "clomiphene": "A medication used to induce ovulation."
}

# --- Model Fallback Layer ---
_active_model = "none"

class FallbackLLM:
    """Wrapper that tries OpenAI first, falls back to local Mistral on any failure."""

    def __init__(self):
        global _active_model
        self._openai = None
        self._mistral = None

        # Initialize OpenAI (gpt-4o-mini for speed/cost similar to flash)
        if os.getenv("OPENAI_API_KEY"):
            try:
                self._openai = ChatOpenAI(model="gpt-4o-mini", temperature=0)
                print("[Model] OpenAI GPT-4o-mini available")
            except Exception as e:
                print(f"[Model] OpenAI init failed: {e}")

        # Initialize local Mistral
        try:
            from langchain_ollama import ChatOllama
            self._mistral = ChatOllama(model="mistral:7b-instruct-q4_K_M", temperature=0)
            print("[Model] Local Mistral 7B Q4 available")
        except Exception as e:
            print(f"[Model] Mistral init failed: {e}")

        if self._openai:
            _active_model = "gpt-4o-mini"
        elif self._mistral:
            _active_model = "mistral-local"
        else:
            _active_model = "none"

    def invoke(self, prompt, **kwargs):
        global _active_model
        # Try OpenAI first
        if self._openai:
            try:
                result = self._openai.invoke(prompt, **kwargs)
                _active_model = "gpt-4o-mini"
                return result
            except Exception as e:
                print(f"[Model] OpenAI call failed ({type(e).__name__}), falling back to Mistral...")

        # Fallback to local Mistral
        if self._mistral:
            try:
                result = self._mistral.invoke(prompt, **kwargs)
                _active_model = "mistral-local"
                return result
            except Exception as e:
                print(f"[Model] Mistral call also failed: {e}")
                raise

        raise RuntimeError("No LLM available. Check OpenAI API key or Ollama installation.")

    async def ainvoke(self, prompt, **kwargs):
        global _active_model
        # Try OpenAI first
        if self._openai:
            try:
                result = await self._openai.ainvoke(prompt, **kwargs)
                _active_model = "gpt-4o-mini"
                return result
            except Exception as e:
                print(f"[Model] OpenAI async call failed ({type(e).__name__}), falling back to Mistral...")

        # Fallback to local Mistral
        if self._mistral:
            try:
                result = await self._mistral.ainvoke(prompt, **kwargs)
                _active_model = "mistral-local"
                return result
            except Exception as e:
                print(f"[Model] Mistral async call also failed: {e}")
                raise

        raise RuntimeError("No LLM available. Check OpenAI API key or Ollama installation.")

llm = FallbackLLM()

async def get_youtube_keywords(query: str) -> str:
    """Extracts core medical keywords from a verbose user query for better YouTube search results."""
    prompt = f"""
    Extract the 2 to 3 most important core medical keywords or conditions from this user query.
    Return ONLY the keywords separated by spaces, nothing else.
    User Query: "{query}"
    """
    try:
        keywords = (await llm.ainvoke(prompt)).content.strip().replace('"', '').replace("'", "")
        return keywords if keywords else query
    except Exception:
        return query

async def contextualize_query(query: str, history: list) -> str:
    """Uses the chat history to rewrite the user's latest query into a standalone search term if needed."""
    if not history:
        return query

    chat_history_str = ""
    # Only use the last 4 messages for context to keep search focused and cheap
    for msg in history[-4:]:
        role = "User" if msg.get("role") == "user" else "Assistant"
        # Truncate very long assistant replies
        text = msg.get("content", "")
        if len(text) > 500:
            text = text[:500] + "..."
        chat_history_str += f"{role}: {text}\n"

    prompt = f"""
    Given the following chat history and a follow-up user query,
    rephrase the follow-up query to be a standalone search query that
    captures all relevant medical context from the history.
    If the follow-up query is already standalone, just return it exactly as is.
    Do NOT answer the query, only return the rephrased standalone query.

    Chat History:
    {chat_history_str}

    Follow-up query: {query}

    Standalone query:"""

    try:
        standalone_query = (await llm.ainvoke(prompt)).content.strip()
        # Clean up quotes if hallucinated
        if standalone_query.startswith('"') and standalone_query.endswith('"'):
            standalone_query = standalone_query[1:-1]
        return standalone_query
    except Exception:
        return query

async def verify_source_content(query: str, url: str, content: str) -> dict:
    """
    Uses the LLM to verify if a single piece of retrieved content is actually relevant
    and reliable for the specific conditions mentioned in the user's query.
    Returns a dictionary with 'is_reliable' (bool) and 'reliability_score' (int).
    """
    verification_prompt = f"""
    You are an expert medical content verifier. Your job is to determine if the provided text
    contains reliable, factual information that specifically addresses the conditions or
    symptoms mentioned in the user's query.

    User Query: "{query}"
    Source URL: {url}
    Content to verify:
    {content}

    Evaluate the content based on factual density, clinical backing, and relevance.
    Note that video content (YouTube, Instagram) may have brief or incomplete descriptions;
    evaluate them fairly based on topical relevance rather than penalizing for brevity.

    Respond ONLY with a valid JSON object in this exact format:
    {{"is_reliable": true/false, "reliability_score": <number 1-100>}}

    Set is_reliable to true IF the content is topically relevant to the query and medically sound.
    You must be lenient towards video/social media transcripts as they lack deep clinical backing.
    """
    try:
        response_text = (await llm.ainvoke(verification_prompt)).content.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]

        result = json.loads(response_text)
        return {
            "is_reliable": result.get("is_reliable", False),
            "reliability_score": result.get("reliability_score", 0)
        }
    except Exception as e:
        # Default to false if verification fails or JSON parsing fails
        return {"is_reliable": False, "reliability_score": 0}

def _normalize_tavily_results(raw):
    """Normalize Tavily results into a list of dicts with 'url' and 'content' keys."""
    if isinstance(raw, dict):
        items = raw.get('results', [])
    elif isinstance(raw, list):
        items = raw
    else:
        return []
    normalized = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(item)
        elif isinstance(item, str):
            normalized.append({"url": item, "content": ""})
    return normalized

MAX_SOURCES = 5
MIN_SOURCES = 2

def _get_source_label(domain: str) -> str:
    """Return a human-friendly label for a domain."""
    labels = {
        "who.int": "World Health Organization",
        "cdc.gov": "Centers for Disease Control",
        "nih.gov": "National Institutes of Health",
        "nhs.uk": "NHS (UK)",
        "mayoclinic.org": "Mayo Clinic",
        "clevelandclinic.org": "Cleveland Clinic",
        "endocrine.org": "Endocrine Society",
        "eshre.eu": "ESHRE",
        "icmr.gov.in": "ICMR India",
        "pubmed.ncbi.nlm.nih.gov": "PubMed Central",
        "ncbi.nlm.nih.gov": "NCBI / PubMed",
        "monash.edu": "Monash University",
        "youtube.com": "YouTube",
        "youtu.be": "YouTube",
    }
    for key, label in labels.items():
        if domain == key or domain.endswith("." + key):
            return label
    return domain.title()


def _select_diverse_sources(validated: list, max_total: int = MAX_SOURCES) -> list:
    """
    Select up to max_total sources. Prefers diversity but does NOT require it.

    Strategy:
    1. Sort all sources by confidence_score descending.
    2. Try to pick one source per unique domain first.
    3. Fill remaining slots from the best remaining sources (may repeat domains).
    4. Try to include 1 VIDEO if available, but do NOT require it.
    5. Even 1 source is valid — no minimum requirement.
    """
    all_sources = list(validated)
    all_sources.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)

    if not all_sources:
        return []

    selected = []
    seen_domains = set()

    # First pass: pick best source from each unique domain (diversity preference)
    for s in all_sources:
        if len(selected) >= max_total:
            break
        domain = s.get("source_domain", "")
        if domain not in seen_domains:
            seen_domains.add(domain)
            selected.append(s)

    # Second pass: fill remaining slots from best remaining sources
    for s in all_sources:
        if len(selected) >= max_total:
            break
        if s not in selected:
            selected.append(s)

    # Try to include 1 video if available and not already included
    has_video = any(s.get("content_type") == "VIDEO" for s in selected)
    if not has_video:
        videos = [s for s in all_sources if s.get("content_type") == "VIDEO" and s not in selected]
        if videos:
            # Replace the lowest-scored article with the best video
            if len(selected) >= max_total:
                selected[-1] = videos[0]
            else:
                selected.append(videos[0])

    print(f"  Diversity: {len(set(s.get('source_domain','') for s in selected))} unique domains, "
          f"{sum(1 for s in selected if s.get('content_type')=='VIDEO')} videos")
    return selected


def search_trusted_sources(query: str) -> dict:
    """
    Three-layer verified medical retrieval pipeline.

    Priority:
    1. Local knowledge base (fastest, pre-scraped trusted content)
    2. Tavily web search fallback (if local KB insufficient)
    3. Auto-cache Tavily results into local KB for future queries

    All layers enforce deterministic domain filtering and confidence scoring.
    """
    import sys
    import os
    pocs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pocs", "womens_health_pcos")
    if pocs_path not in sys.path:
        sys.path.insert(0, pocs_path)

    try:
        from retrieval.domain_filter import filter_by_domain
        from retrieval.content_classifier import classify_results
        from retrieval.confidence_scoring import score_results
        from retrieval.constraints_validator import validate_batch
        from storage.local_kb import search as kb_search, store_batch

        print(f"\n[Pipeline] Query: {query}")
        print(f"[Pipeline] Model: {_active_model}")

        # === Layer 1: Local Knowledge Base ===
        print("[Layer 1: Local KB]")
        local_results = kb_search(query, limit=10)
        print(f"  Found {len(local_results)} local sources.")

        if len(local_results) >= 2:
            # Enough local sources — skip Tavily entirely
            print(f"  ✓ Using local KB (skipping Tavily)")
            diverse = _select_diverse_sources(local_results)
            return _build_response(diverse, query, source_layer="local_kb")

        # === Layer 2: Tavily Fallback ===
        print("[Layer 2: Tavily Fallback]")
        try:
            from retrieval.tavily_search import MedicalSearchEngine
            engine = MedicalSearchEngine(max_results=20)
            raw_results = engine.search(query)
            print(f"  Tavily returned {len(raw_results)} raw results.")
        except Exception as e:
            print(f"  Tavily failed: {e}")
            raw_results = []

        if not raw_results and not local_results:
            return {"context": "No verified medical sources found for this query.", "source_urls": []}

        # Filter Tavily results through the deterministic pipeline
        tavily_validated = []
        if raw_results:
            filtered, _ = filter_by_domain(raw_results)
            print(f"  {len(filtered)} passed domain filter.")

            if filtered:
                classified = classify_results(filtered)
                scored = score_results(classified)
                tavily_validated, _ = validate_batch(scored)
                print(f"  {len(tavily_validated)} passed constraints.")

                # Auto-cache into local KB for future queries
                if tavily_validated:
                    cache_records = []
                    for r in tavily_validated:
                        cache_records.append({
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "source_domain": r.get("source_domain", ""),
                            "content_type": r.get("content_type", "ARTICLE"),
                            "content": r.get("content", ""),
                            "confidence_level": r.get("confidence_level", "MEDIUM"),
                            "confidence_score": r.get("confidence_score", 70),
                            "query_topics": query,
                            "source_label": _get_source_label(r.get("source_domain", "")),
                        })
                    cached = store_batch(cache_records)
                    print(f"  Cached {cached} new sources to local KB.")

        # Combine local + Tavily results (dedup by URL)
        all_results = list(local_results)
        seen_urls = {r.get("url", "") for r in all_results}
        for r in tavily_validated:
            if r.get("url", "") not in seen_urls:
                all_results.append(r)
                seen_urls.add(r.get("url", ""))

        if not all_results:
            return {"context": "No verified medical sources found for this query.", "source_urls": []}

        # Diversity selection
        diverse = _select_diverse_sources(all_results)
        layer = "local_kb+tavily" if local_results and tavily_validated else "tavily"
        return _build_response(diverse, query, source_layer=layer)

    except Exception as e:
        print(f"Error during pipeline: {e}")
        import traceback
        traceback.print_exc()
        return {"context": "Search failed. Please try again later.", "source_urls": []}


def _build_response(sources: list, query: str, source_layer: str = "unknown") -> dict:
    """Build the final context and source_urls from a list of validated sources."""
    context_parts = []
    source_urls = []

    print(f"[Building Response] {len(sources)} sources from {source_layer}")
    for doc in sources:
        url = doc.get("url", "")
        content = doc.get("content", "")
        title = doc.get("title", "") or url.split("/")[-1].replace("-", " ").title()
        content_type = doc.get("content_type", "ARTICLE")
        domain = doc.get("source_domain", get_domain_from_url(url))
        source_label = doc.get("source_label", "") or _get_source_label(domain)
        confidence = doc.get("confidence_score", 50)
        conf_level = doc.get("confidence_level", "MEDIUM")

        type_tag = "VIDEO" if content_type == "VIDEO" else "ARTICLE"
        context_parts.append(
            f"[Source {len(source_urls)+1}] ({type_tag}) {title}\n"
            f"Source: {source_label} | Confidence: {confidence}\n"
            f"URL: {url}\n"
            f"Content: {content}"
        )
        source_urls.append({
            "url": url,
            "score": confidence,
            "type": content_type.lower(),
            "title": title,
            "source_label": source_label,
            "confidence_level": conf_level,
        })

    if not context_parts:
        return {"context": "No verified medical sources found for this query.", "source_urls": []}

    context = "\n\n".join(context_parts)
    print(f"  → Returning {len(source_urls)} sources | Layer: {source_layer} | Model: {_active_model}")
    return {"context": context, "source_urls": source_urls}

# --- 3. The Strict System Prompt ---
system_prompt = """You are a trusted healthcare information assistant called Dory.
Your role is to provide clear, educational health information grounded only in verified medical sources.

Response Guidelines:
- Write in clear, accessible language that a general audience can understand.
- Structure your response with short paragraphs and headers when covering multiple topics.
- Summarize research findings in simple terms, avoiding unnecessary jargon.
- Always cite your sources inline using the [Source N] labels (e.g., "According to [Source 1], ...").
- When citing a video source, mention it is a video (e.g., "As explained in the video [Source 3], ...").

Source Rules:
- Use ONLY the verified sources provided in the context below.
- Each source has a type (ARTICLE or VIDEO), a confidence score, and a publication source.
- Prioritize higher confidence sources when information conflicts.
- If the context does not contain sufficient information, explicitly state: "I don't have enough verified information on this specific topic. Please consult a healthcare provider."

You must NEVER:
- Diagnose medical conditions
- Recommend specific medications or treatments
- Claim medical certainty
- Hallucinate facts or fabricate sources
- Use information not present in the provided context

All information is educational only. Always recommend consulting a healthcare professional for personal medical decisions.

Provided Context (Verified Sources):
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{query}")
])

# LLM initialized above for use in verification

# --- 5. Main Interaction Function ---

def run_prescription_pipeline(extracted_json_str: str) -> dict:
    import json
    try:
        data = json.loads(extracted_json_str)
    except Exception as e:
        return {"context": "Failed to parse OCR data.", "source_urls": []}

    output_lines = []
    topics_for_search = []
    
    def _extract_text(item):
        if isinstance(item, dict):
            # Try to grab common keys the model might hallucinate
            return str(item.get("name", item.get("condition", item.get("value", item.get("instruction", " ".join(str(v) for v in item.values()))))))
        return str(item)

    # Process Medicines
    medicines = data.get("medicines", [])
    if medicines:
        output_lines.append("### Medicines\n")
        for med in medicines:
            med_str = _extract_text(med)
            med_lower = med_str.lower().strip()
            explanation = "A medication name was detected in the prescription."
            for key, val in medicine_db.items():
                if key in med_lower:
                    explanation = val
                    topics_for_search.append(key)
                    break
            output_lines.append(f"- **{med_str}**\n  *Explanation: {explanation}*\n")

    # Process Conditions
    conditions = data.get("conditions", [])
    if conditions:
        output_lines.append("### Conditions\n")
        for cond in conditions:
            cond_str = _extract_text(cond)
            cond_lower = cond_str.lower().strip()
            explanation = "This may refer to a medical condition or symptom."
            for key, val in medical_terms_db.items():
                if key in cond_lower:
                    explanation = val
                    topics_for_search.append(key)
                    break
            output_lines.append(f"- **{cond_str}**\n  *Explanation: {explanation}*\n")

    # Process Lab Values
    labs = data.get("lab_values", [])
    if labs:
        output_lines.append("### Lab Values\n")
        for lab in labs:
            lab_str = _extract_text(lab)
            lab_lower = lab_str.lower().strip()
            explanation = "This value is commonly associated with laboratory test results."
            for key, val in medical_terms_db.items():
                if key in lab_lower:
                    explanation = f"This test is often used to evaluate {key.upper()}: {val}"
                    topics_for_search.append(key)
                    break
            output_lines.append(f"- **{lab_str}**\n  *Explanation: {explanation}*\n")

    # Process Doctor Instructions
    instructions = data.get("doctor_instructions", [])
    if instructions:
        output_lines.append("### Doctor Instructions\n")
        for inst in instructions:
            inst_str = _extract_text(inst)
            inst_lower = inst_str.lower().strip()
            explanation = "An instruction noted by the doctor."
            for key, val in medical_terms_db.items():
                if key in inst_lower:
                    explanation = val
                    topics_for_search.append(key)
                    break
            output_lines.append(f"- **{inst_str}**\n  *Explanation: {explanation}*\n")

    disclaimer = "\n> **Disclaimer:** This information is educational and does not replace professional medical advice. Always consult your healthcare provider for actual medical interpretation and treatment."
    
    output_lines.append(disclaimer)
    context = "\n".join(output_lines)
    
    # Fetch optional references using Tavily via search_trusted_sources
    source_urls = []
    if topics_for_search:
        search_query = " ".join(topics_for_search[:2]) + " meaning explanation"
        results = search_trusted_sources(search_query)
        source_urls = results.get("source_urls", [])

    return {
        "context": context,
        "source_urls": source_urls
    }

async def ask_health_assistant(query: str, history: list = None) -> dict:
    """Main function to interact with the assistant. Returns dict with response and sources."""
    try:
        history = history or []
        
        if query.startswith("I uploaded my prescription"):
            # Extract JSON from the query
            import re
            match = re.search(r"Here is what was extracted:\n\n(.*?)\n\nPlease explain", query, re.DOTALL)
            if match:
                extracted_json_str = match.group(1).strip()
                # Run the targeted prescription pipeline
                result = run_prescription_pipeline(extracted_json_str)
                return {
                    "response": result["context"],
                    "sources": result["source_urls"]
                }
            else:
                return {
                    "response": "Error: Could not parse prescription data. Please ensure it was successfully extracted.",
                    "sources": []
                }

        # Step 1: Contextualize the query against history so the search engine works properly
        standalone_query = await contextualize_query(query, history)
        if standalone_query != query:
            print(f"\n[Contextualized Query for Search: '{standalone_query}']")

        # Step 2: Search trusted sources using the standalone query
        search_results = search_trusted_sources(standalone_query)
        context = search_results["context"]
        source_urls = search_results["source_urls"]

        # Formulate history for LangChain
        formatted_history = []
        if history:
            for msg in history[-6:]: # Keep the window sane
                if msg.get("role") == "user":
                    formatted_history.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    formatted_history.append(AIMessage(content=msg.get("content", "")))

        # Step 3: Format the prompt with context, query, and chat_history
        formatted_prompt = prompt.format_messages(
            context=context,
            query=query,
            chat_history=formatted_history
        )

        # Step 4: Get LLM response
        response = await llm.ainvoke(formatted_prompt)
        response_text = response.content

        return {
            "response": response_text,
            "sources": source_urls
        }

    except Exception as e:
        error_msg = f"System Error: Please ensure your API keys are set correctly. Error details: {e}"
        print(f"\n{error_msg}")
        return {
            "response": error_msg,
            "sources": []
        }

# --- 6. Prescription OCR Analysis ---
async def analyze_prescription(base64_images: list[str]) -> dict:
    """Analyze one or more prescription images using OpenAI Vision and extract structured information."""
    try:
        client = AsyncOpenAI()

        image_count = len(base64_images)
        if image_count == 1:
            prompt_text = "Please read and extract all information from this prescription image."
        else:
            prompt_text = (
                f"I am uploading {image_count} images. They may be multiple pages of the same prescription "
                "or separate prescriptions. Please read and extract all information from every image. "
                "If they appear to be pages of the same prescription, combine the information. "
                "If they are separate prescriptions, clearly label each one."
            )

        content = [{"type": "text", "text": prompt_text}]
        for img in base64_images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img}"}
            })

        max_tokens = min(1000 * image_count, 4000)

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a medical prescription reader. Analyze the prescription image(s) and extract the information into a strict JSON format.\n"
                        "Return ONLY a JSON object with this exact structure:\n"
                        "{\n"
                        '  "medicines": [],\n'
                        '  "conditions": [],\n'
                        '  "lab_values": [],\n'
                        '  "doctor_instructions": []\n'
                        "}\n\n"
                        "If multiple images are provided, they may be pages of the same prescription or separate prescriptions. "
                        "Handle both cases appropriately.\n"
                        "Do NOT provide medical advice or interpretations beyond what is written."
                    )

                },
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=max_tokens,
            temperature=0
        )
        
        extracted_text = response.choices[0].message.content
        return {"success": True, "extracted_text": extracted_text}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- 7. PCOS Pattern Evaluation ---
def evaluate_pcos(user_data: dict) -> dict:
    """
    Evaluates a user questionnaire profile (age, weight, cycles, symptoms), 
    determines patterns, provides risk awareness scores, 
    and fetches structured educational content mapped to those patterns.
    """
    from pocs.womens_health_pcos.assessment.content_mapper import evaluate_pcos_patterns
    return evaluate_pcos_patterns(user_data)


# --- 8. Interactive Testing Loop ---
if __name__ == "__main__":
    async def main():
        print("\n" + "*" * 60)
        print("Healthcare Information Assistant (Prototype)")
        print("Type 'exit' or 'quit' to stop.")
        print("Remember to set OPENAI_API_KEY and TAVILY_API_KEY in your environment or a .env file.")
        print("*" * 60 + "\n")

        while True:
            user_input = input("Ask a health-related question: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input.strip():
                continue

            await ask_health_assistant(user_input)

    asyncio.run(main())
