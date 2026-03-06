import sys
import os
sys.path.append(os.getcwd())
import medical_assistant
import json

history = []
q1 = "I am feeling dizzy and have high sugar and high BP"
print(f"\nUser Q1: {q1}")
res1 = medical_assistant.ask_health_assistant(q1, history)
print(f"Assistant R1 generated with {len(res1['sources'])} sources.")

history.append({"role": "user", "content": q1})
history.append({"role": "assistant", "content": res1["response"]})

q2 = "Are there any dietary changes I should make for it?"
print(f"\nUser Q2 (Follow-up): {q2}")
res2 = medical_assistant.ask_health_assistant(q2, history)
print("\nFinal Follow-up Response (Truncated):")
print(res2["response"][:300] + "...\n")
print(f"Final Follow-up Sources output length: {len(res2['sources'])}")
