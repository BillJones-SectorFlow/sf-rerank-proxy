from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv
import os
import time

# Load environment variables from .env
load_dotenv()

app = FastAPI()

# --- FINAL FIX ---
# The Pydantic model now correctly expects a field named "model"
# to match the incoming request data revealed by the logs.
class RerankRequest(BaseModel):
    model: str  # Changed from model_id: str = Field(alias="model-id")
    query: str
    documents: list[str]

@app.post("/rerank")
async def rerank(request: RerankRequest):
    endpoint = os.getenv("RUNPOD_ENDPOINT")
    api_key = os.getenv("RUNPOD_API_KEY")

    if not endpoint or not api_key:
        raise HTTPException(status_code=500, detail="Missing RUNPOD_ENDPOINT or RUNPOD_API_KEY")

    runpod_payload = {
        "input": {
            "model": "michaelfeil/mxbai-rerank-large-v2-seq",
            "query": request.query,
            "documents": request.documents
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=runpod_payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Error contacting backend service: {e}")
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid JSON response from backend service")

    try:
        runpod_result = data["output"][0]
        translated_results = []
        for res in runpod_result["results"]:
            translated_results.append({
                "relevance_score": res["relevance_score"],
                "index": res["index"],
                "document": None
            })

        final_response = {
            "id": data.get("id", f"proxy-{int(time.time())}"),
            "object": "rerank",
            "results": translated_results,
            # --- FINAL FIX ---
            # Use request.model to match the updated Pydantic model field name
            "model": request.model,
            "usage": runpod_result["usage"],
            "created": int(time.time())
        }
        return final_response
    except (KeyError, TypeError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse backend response. Malformed data: {e}")
