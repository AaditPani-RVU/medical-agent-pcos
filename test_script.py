import sys
import os
sys.path.append(os.getcwd())
import medical_assistant
import json

keywords_prompt = f"""
Extract the 2 to 3 most important core medical keywords or conditions from this user query.
Return ONLY the keywords separated by spaces, nothing else.
User Query: "I am feeling dizzy and have high sugar and high BP"
"""
keywords = medical_assistant.llm.invoke(keywords_prompt).content.strip().replace('"', '')
print(f"Keywords: {keywords}")

yt_query = f"{keywords} Mayo Clinic"
print(f"YT Query: {yt_query}")

raw_yt_results = medical_assistant.youtube_search.run(f"{yt_query}, 3")
print(f"YT Results: {raw_yt_results}")
