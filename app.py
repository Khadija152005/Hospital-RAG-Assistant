import sys
import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

# Add rag_component to Python path so its internal imports work correctly
sys.path.append(os.path.join(os.path.dirname(__file__), "rag_component"))

# Now we can safely import from rag_component
from rag_component.main import handle_technical_query_verbose

app = FastAPI(title="Hospital AI Central")

class QueryRequest(BaseModel):
    question: str
    asset_id: Optional[str] = None

class SettingsRequest(BaseModel):
    groq_api_key: str

@app.post("/api/chat")
def chat(request: QueryRequest):
    try:
        # Call the existing RAG function
        result = handle_technical_query_verbose(request.question, request.asset_id)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
def update_settings(request: SettingsRequest):
    try:
        from dotenv import set_key
        # Target the .env file in the main directory
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        set_key(env_path, "GROQ_API_KEY", request.groq_api_key)
        
        # Update the active environment variable immediately
        os.environ["GROQ_API_KEY"] = request.groq_api_key
        
        # Also update the loaded config module directly
        import rag_component.config as config
        config.GROQ_API_KEY = request.groq_api_key
        
        return {"status": "success"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Future API routes can go here (e.g., @app.post("/api/inventory"))

# Mount the frontend website directory at the root
app.mount("/", StaticFiles(directory="website", html=True), name="website")

if __name__ == "__main__":
    import uvicorn
    # Start the server locally
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
