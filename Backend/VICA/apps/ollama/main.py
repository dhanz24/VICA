import os
import sys
import json
import logging
import subprocess
from typing import Optional, Union
from fastapi import FastAPI, HTTPException, Request, Response, Depends, APIRouter, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

OLLAMA_BASE_URLS = os.getenv("OLLAMA_BASE_URLS", "http://localhost:11434")
CORS_ALLOW_ORIGIN = os.getenv("CORS_ALLOW_ORIGIN", "*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ollama-api")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from VICA.apps.VICA.utils.auth import get_verified_user, get_admin_user


# Base models
class GenerateCompletionForm(BaseModel):
    model: str
    prompt: str
    images: Optional[list[str]] = None
    format: Optional[str] = None
    options: Optional[dict] = None
    system: Optional[str] = None
    template: Optional[str] = None
    context: Optional[str] = None
    stream: Optional[bool] = True
    raw: Optional[bool] = None
    keep_alive: Optional[Union[int, str]] = None


class ChatMessage(BaseModel):
    role: str
    content: str
    images: Optional[list[str]] = None


class GenerateChatCompletionForm(BaseModel):
    model: str
    messages: list[ChatMessage]
    format: Optional[str] = None
    options: Optional[dict] = None
    template: Optional[str] = None
    stream: Optional[bool] = None
    keep_alive: Optional[Union[int, str]] = None


# Initialize FastAPI app
app = FastAPI(
    title="Ollama API",
    docs_url="/docs",
)

# Initialize models list
app.state.MODELS = {}

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ALLOW_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to check URLs
@app.middleware("http")
async def check_url(request: Request, call_next):
    if len(app.state.MODELS) == 0:
        await get_models()
    response = await call_next(request)
    return response

# Utility functions
async def fetch_model_list():
    """Fetch list of installed models."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_BASE_URLS}/api/tags") as response:
                response.raise_for_status()
                return await response.json()
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch models")

async def fetch_model_info(model_id: str):
    """Fetch information about a specific model."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_BASE_URLS}/api/models/{model_id}") as response:
                response.raise_for_status()
                return await response.json()
    except Exception as e:
        logger.error(f"Failed to fetch model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch model info")

async def fetch_embed(data: dict):
    """Fetch embeddings from model API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{OLLAMA_BASE_URLS}/api/embeddings", json=data) as response:
                response.raise_for_status()
                return await response.json()
    except Exception as e:
        logger.error(f"Failed to fetch embeddings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch embeddings")

# Endpoints
@app.get("/")
async def get_status():
    return {"status": True}

@app.get("/models")
async def get_models(user=Depends(get_verified_user)):
    models = await fetch_model_list()
    return models

@app.get("/models/{model_id}")
async def get_model_info(model_id: str):
    model_info = await fetch_model_info(model_id)
    return model_info

@app.post("/embed")
async def generate_embeddings(data: GenerateCompletionForm):
    payload = {**data.model_dump(exclude_none=True)}
    embeddings = await fetch_embed(payload)
    return embeddings

async def cleanup_response(response, session):
    if response:
        response.close()
    if session:
        await session.close()

# Helper function
async def post_streaming_url(
    url: str, payload: Union[str, bytes], stream: bool = True, content_type=None
):
    async with aiohttp.ClientSession(
        trust_env=True, 
        timeout=aiohttp.ClientTimeout(total=30)
    ) as session:
        try:
            async with session.post(url, data=payload, headers={"Content-Type": "application/json"}) as r:
                r.raise_for_status()

                if stream:
                    headers = dict(r.headers)
                    if content_type:
                        headers["Content-Type"] = content_type
                    return StreamingResponse(
                        r.content,
                        status_code=r.status,
                        headers=headers,
                    )
                else:
                    res = await r.json()
                    return res
        except Exception as e:
            error_detail = "Connection error"
            if 'r' in locals() and r:
                try:
                    res = await r.json()
                    if "error" in res:
                        error_detail = res['error']
                except Exception:
                    error_detail = f"Ollama: {e}"

            raise HTTPException(status_code=r.status if 'r' in locals() and r else 500, detail=error_detail)

# Endpoint for generating text completion
@app.post("/api/generate")
@app.post("/api/generate/{url_idx}")
async def generate_completion(
    form_data: GenerateCompletionForm,
    url_idx: Optional[int] = None,
    user=Depends(get_verified_user),
):
    model = form_data.model

    if ":" not in model:
        model = f"{model}:latest"

    # Assuming `app.state.MODELS` is available and contains models and URLs
    # if model in app.state.MODELS:
    #     url_idx = random.choice(app.state.MODELS[model]["urls"])
    # else:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Model {form_data.model} not found",
    #     )

    url = OLLAMA_BASE_URLS
    payload = form_data.model_dump_json(exclude_none=True).encode()

    return await post_streaming_url(f"{url}/api/generate", payload)

# Endpoint for generating chat completion
@app.post("/api/chat")
@app.post("/api/chat/{url_idx}")
async def generate_chat_completion(
    form_data: GenerateChatCompletionForm,
    url_idx: Optional[int] = None,
    user=Depends(get_verified_user),
):
    payload = form_data.model_dump(exclude_none=True)
    model_id = form_data.model

    if ":" not in model_id:
        model_id = f"{model_id}:latest"

    # if model_id in app.state.MODELS:
    #     url_idx = random.choice(app.state.MODELS[model_id]["urls"])
    # else:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Model {model_id} not found",
    #     )

    url = OLLAMA_BASE_URLS
    return await post_streaming_url(
        f"{url}/api/chat", json.dumps(payload), stream=form_data.stream, content_type="application/x-ndjson"
    )