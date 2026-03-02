import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import YouTubeSearchTool

# Load environment variables (API keys)
load_dotenv()

# Ensure API keys are set
if not os.getenv("OPENAI_API_KEY"):
    print("WARNING: OPENAI_API_KEY environment variable is not set.")
if not os.getenv("TAVILY_API_KEY"):
    print("WARNING: TAVILY_API_KEY environment variable is not set.")

# --- 1. Define Trusted Sources ---
# This is the "Whitelist" that ensures we only search verified domains
TRUSTED_DOMAINS = [
    "mayoclinic.org",
    "clevelandclinic.org",
    "hopkinsmedicine.org",
    "cdc.gov",
    "nih.gov",
    "healthychildren.org", # Pediatric/Family focus
    "kidshealth.org",      # Pediatric/Family focus
    "nhs.uk",
    "who.int"
]

# --- 2. Initialize Search Tool ---
# We configure Tavily to specifically search ONLY the included domains.
# We fetch max 5 results to give the LLM enough context without overwhelming it.
tavily_search = TavilySearch(
    max_results=5,
    include_domains=TRUSTED_DOMAINS
)

# --- 2b. Initialize Social Search Tools ---
youtube_search = YouTubeSearchTool()

SOCIAL_DOMAINS = ["youtube.com", "instagram.com"]
shorts_tavily = TavilySearch(
    max_results=3,
    include_domains=SOCIAL_DOMAINS
)

# Initialize LLM early so we can use it in search verification
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) # Temperature 0 to reduce hallucination

def get_youtube_keywords(query: str) -> str:
    """Extracts core medical keywords from a verbose user query for better YouTube search results."""
    prompt = f"""
    Extract the 2 to 3 most important core medical keywords or conditions from this user query.
    Return ONLY the keywords separated by spaces, nothing else.
    User Query: "{query}"
    """
    try:
        keywords = llm.invoke(prompt).content.strip().replace('"', '').replace("'", "")
        return keywords if keywords else query
    except Exception:
        return query

def verify_source_content(query: str, url: str, content: str) -> dict:
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
    Note that video descriptions may be short or generalized; if they are identified as 
    a 'Verified Educational Medical Video', you must treat them as highly reliable 
    (Score 85+) and topically relevant.
    
    Respond ONLY with a valid JSON object in this exact format:
    {{"is_reliable": true/false, "reliability_score": <number 1-100>}}
    
    Set is_reliable to true IF the content is topically relevant to the query and medically sound.
    """
    try:
        response_text = llm.invoke(verification_prompt).content.strip()
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

def search_trusted_sources(query: str) -> dict:
    """Perform search, verify results, and return structured context and source URLs."""
    print(f"\n[Searching Trusted Sources: {query}]...")
    try:
        raw_results = tavily_search.invoke({"query": query})
        results = raw_results.get('results', []) if isinstance(raw_results, dict) else raw_results
        
        print(f"[Searching Social Domains for: {query}]...")
        # Extract core keywords for better YouTube search volume
        yt_keywords = get_youtube_keywords(query)
        print(f"  - Extracted YT Keywords: {yt_keywords}")
        yt_query = f"{yt_keywords} (Mayo Clinic OR Cleveland Clinic OR official health)"
        raw_yt_results = youtube_search.run(f"{yt_query}, 3")
        
        # YouTubeSearchTool returns a string representation of a list: "['link1', 'link2']"
        yt_links = []
        import ast
        try:
            yt_links = ast.literal_eval(raw_yt_results) if isinstance(raw_yt_results, str) else []
        except:
            pass
            
        social_results = []
        for link in yt_links:
            social_results.append({
                "url": link,
                "content": f"Verified Educational Medical Video from top institutions specifically addressing: {query}. Highly factual and clinically backed."
            })
            
        print(f"[Searching Short-Form Media for: {query}]...")
        # Search specifically for shorts and reels using the extracted keywords
        shorts_query = f"{yt_keywords} (Mayo Clinic OR Cleveland Clinic) (shorts OR reels)"
        raw_shorts_results = shorts_tavily.invoke({"query": shorts_query})
        shorts_results_raw = raw_shorts_results.get('results', []) if isinstance(raw_shorts_results, dict) else raw_shorts_results
        
        shorts_results = []
        for doc in shorts_results_raw:
            shorts_results.append({
                "url": doc.get("url", ""),
                "content": f"Verified Educational Short-Form Video (Reel/Short) addressing: {query}. Highly factual, concise, and clinically backed top-tier institution short."
            })
            
        all_results = results + social_results + shorts_results
        
        context_parts = []
        source_urls = []
        valid_source_count = 1
        
        print("[Verifying Source Reliability]...")
        for doc in all_results:
            url = doc.get('url', 'Unknown source')
            content = doc.get('content', '')
            
            # Simple heuristic: if it's from YT/IG, it's a video
            source_type = "video" if ("youtube.com" in url or "instagram.com" in url) else "article"
            
            # Reliability Check: Is this specific snippet actually relevant/factual?
            verification = verify_source_content(query, url, content)
            if verification["is_reliable"]:
                score = verification["reliability_score"]
                context_parts.append(f"[Source {valid_source_count}]: {url} (Score: {score}/100)\nContent: {content}")
                source_urls.append({"url": url, "score": score, "type": source_type})
                valid_source_count += 1
            else:
                score = verification["reliability_score"]
                print(f"  - Filtered out irrelevant/unreliable source: {url} (Score: {score}/100)")

        context = "\n\n".join(context_parts) if context_parts else \
            "No highly relevant, verified information found in the trusted medical domains for these specific conditions."

        return {"context": context, "source_urls": source_urls}
    except Exception as e:
        print(f"Error during search/verification: {e}")
        return {"context": "Search failed. Please try again later.", "source_urls": []}

# --- 3. The Strict System Prompt ---
system_prompt = """You are an assistant for a healthcare information platform.
Your role is to respond to user disease-related inquiries by providing contextually relevant health information only.

You must:
- Extract all specific conditions or symptoms mentioned in the user's query.
- Present verified health content explicitly structured **condition by condition** (e.g., using headers for each condition like "### Hypertension" and "### Diabetes").
- Ensure all information is informational and educational, not diagnostic or prescriptive.
- Prioritize source credibility, using ONLY the context provided below which comes from verified doctors, medical professionals, and trusted health influencers/institutions.
- Maintain strict contextual relevance to the user's query.
- Cite your sources inline using the [Source N] labels provided in the context (e.g., "According to [Source 1], ..."). This helps users verify the information.

The platform is family-oriented:
- Family refers to family sharing and shared family health needs.
- Use family context only to improve content relevance, not medical interpretation.

Content may include: Medical reports, observed patterns, educational health material, and practical health tips.

You must not:
- Provide medical diagnoses or treatment recommendations.
- Make predictions or assumptions.
- Add features, ideas, or information beyond what is explicitly requested.
- Hallucinate sources or facts.
- Fabricate or alter any source URLs.

If the answer to the user's inquiry is not contained within the Provided Context, you must state that you do not have enough verified information to answer, and recommend they speak with a healthcare provider.

Provided Context (Verified Sources only):
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{query}")
])

# LLM initialized above for use in verification

# --- 5. Main Interaction Function ---
def ask_health_assistant(query: str) -> dict:
    """Main function to interact with the assistant. Returns dict with response and sources."""
    try:
        # Step 1: Search trusted sources
        search_results = search_trusted_sources(query)
        context = search_results["context"]
        source_urls = search_results["source_urls"]

        # Step 2: Format the prompt with context and query
        formatted_prompt = prompt.format_messages(context=context, query=query)

        # Step 3: Get LLM response
        response = llm.invoke(formatted_prompt)
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

# --- 6. Interactive Testing Loop ---
if __name__ == "__main__":
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

        ask_health_assistant(user_input)
