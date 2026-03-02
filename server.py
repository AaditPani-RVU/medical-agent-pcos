from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

from medical_assistant import ask_health_assistant

app = FastAPI(title="Medical Assistant API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

class SourceItem(BaseModel):
    url: str
    score: int
    type: str

class ChatResponse(BaseModel):
    response: str
    sources: list[SourceItem]

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = ask_health_assistant(request.query)
    return ChatResponse(
        response=result.get("response", "Error generating response."),
        sources=result.get("sources", [])
    )

# Serve the static frontend files
frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if not os.path.exists(frontend_path):
    print(f"Warning: Frontend build directory not found at {frontend_path}. Please build the React app.")
else:
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    print("Starting Medical Assistant Server on http://localhost:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
