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

def search_trusted_sources(query: str) -> dict:
    """Perform search and return structured results with context and source URLs."""
    print(f"\n[Searching Trusted Sources: {query}]...")
    try:
        raw_results = tavily_search.invoke({"query": query})
        # TavilySearch returns a dict with 'results' key containing the list
        results = raw_results.get('results', []) if isinstance(raw_results, dict) else raw_results
        # Build context string for the LLM and collect source URLs
        context_parts = []
        source_urls = []
        for i, doc in enumerate(results, 1):
            url = doc.get('url', 'Unknown source')
            content = doc.get('content', '')
            context_parts.append(f"[Source {i}]: {url}\nContent: {content}")
            source_urls.append(url)

        context = "\n\n".join(context_parts) if context_parts else \
            "No highly relevant information found in the trusted medical domains for this query."

        return {"context": context, "source_urls": source_urls}
    except Exception as e:
        print(f"Error during search: {e}")
        return {"context": "Search failed. Please try again later.", "source_urls": []}

# --- 3. The Strict System Prompt ---
system_prompt = """You are an assistant for a healthcare information platform.
Your role is to respond to user disease-related inquiries by providing contextually relevant health information only.

You must:
- Present verified health content related to the disease being inquired about.
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

Provided Context (Verified Sources):
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{query}")
])

# --- 4. Initialize LLM ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) # Temperature 0 to reduce hallucination

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
