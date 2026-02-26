import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate

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

# Initialize LLM early so we can use it in search verification
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) # Temperature 0 to reduce hallucination

def verify_source_content(query: str, url: str, content: str) -> bool:
    """
    Uses the LLM to verify if a single piece of retrieved content is actually relevant
    and reliable for the specific conditions mentioned in the user's query.
    """
    verification_prompt = f"""
    You are a medical content verifier. Your job is to determine if the provided text 
    contains reliable, factual information that specifically addresses the conditions or 
    symptoms mentioned in the user's query.
    
    User Query: "{query}"
    Source URL: {url}
    Content to verify: 
    {content}
    
    Does this content contain specific, factual, and relevant health information about 
    the conditions mentioned in the query? 
    Respond with ONLY 'YES' or 'NO'.
    """
    try:
        response = llm.invoke(verification_prompt).content.strip().upper()
        return response.startswith('YES')
    except Exception:
        # Default to false if verification fails to enforce strict reliability
        return False

def search_trusted_sources(query: str) -> dict:
    """Perform search, verify results, and return structured context and source URLs."""
    print(f"\n[Searching Trusted Sources: {query}]...")
    try:
        raw_results = tavily_search.invoke({"query": query})
        results = raw_results.get('results', []) if isinstance(raw_results, dict) else raw_results
        
        context_parts = []
        source_urls = []
        valid_source_count = 1
        
        print("[Verifying Source Reliability]...")
        for doc in results:
            url = doc.get('url', 'Unknown source')
            content = doc.get('content', '')
            
            # Reliability Check: Is this specific snippet actually relevant/factual?
            if verify_source_content(query, url, content):
                context_parts.append(f"[Source {valid_source_count}]: {url}\nContent: {content}")
                source_urls.append(url)
                valid_source_count += 1
            else:
                print(f"  - Filtered out irrelevant/unreliable source: {url}")

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
def ask_health_assistant(query: str):
    """Main function to interact with the assistant."""
    print("=" * 60)
    print(f"USER QUERY: {query}")
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

        # Step 4: Display the response
        print("\n--- ASSISTANT RESPONSE ---\n")
        print(response_text)

        # Step 5: Display verified source URLs for transparency
        if source_urls:
            print("\n--- VERIFIED SOURCES ---")
            for i, url in enumerate(source_urls, 1):
                print(f"  [Source {i}]: {url}")

        print("\n" + "=" * 60 + "\n")
    except Exception as e:
        print(f"\nSystem Error: Please ensure your API keys are set correctly. Error details: {e}")

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
