from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import base64

from medical_assistant import ask_health_assistant, analyze_prescription

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
    history: Optional[List[Dict[str, Any]]] = []

class SourceItem(BaseModel):
    url: str
    score: int
    type: str

class ChatResponse(BaseModel):
    response: str
    sources: list[SourceItem]

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await ask_health_assistant(request.query, request.history)
    return ChatResponse(
        response=result.get("response", "Error generating response."),
        sources=result.get("sources", [])
    )

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB

@app.post("/api/upload_prescription")
async def upload_prescription(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    base64_images = []
    for file in files:
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail=f"File '{file.filename}': Only JPEG, PNG, and WebP images are supported.")

        contents = await file.read()
        if len(contents) > MAX_SIZE:
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' exceeds 10MB limit.")

        base64_images.append(base64.b64encode(contents).decode("utf-8"))

    result = await analyze_prescription(base64_images)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"OCR failed: {result['error']}")

    return {"extracted_text": result["extracted_text"]}

# Serve the static frontend files
frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if not os.path.exists(frontend_path):
    print(f"Warning: Frontend build directory not found at {frontend_path}. Please build the React app.")
else:
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    print("Starting Medical Assistant Server on http://localhost:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
