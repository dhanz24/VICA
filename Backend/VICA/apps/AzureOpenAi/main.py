import os
import sys
import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

import openai
import aiohttp
import requests
from dotenv import load_dotenv

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

load_dotenv('.env')

AZURE_OPENAI_BASE_URL = os.getenv("AZURE_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_API_VERSION")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")
AZURE_OPENAI_MODEL_NAME = os.getenv("MODEL_NAME")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from VICA.apps.VICA.utils.auth import get_current_user, get_verified_user, get_admin_user

CORS_ALLOW_ORIGIN = os.getenv("CORS_ALLOW_ORIGIN", "*")

app = FastAPI(
    title="Azure OpenAI API",
    docs_url="/docs",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGIN,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.MODELS = {}

@app.middleware("http")
async def check_url(request: Request, call_next):
    if len(app.state.MODELS) == 0:
        await get_models()
    response = await call_next(request)
    return response

async def fetch_url(url, key):
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        headers = {"Authorization": f"Bearer {key}"}
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.get(url, headers=headers) as response:
                return await response.json()
    except Exception as e:
        # Handle connection error here
        log.error(f"Connection error: {e}")
        return None

async def cleanup_response(
    response: Optional[aiohttp.ClientResponse],
    session: Optional[aiohttp.ClientSession],
):
    if response:
        response.close()
    if session:
        await session.close()

# async def get_models():
#     url = f"{AZURE_OPENAI_BASE_URL}/models?api-version={AZURE_OPENAI_API_VERSION}"
#     response = await fetch_url(url, AZURE_OPENAI_API_KEY)
#     if response:
#         models = response.get("models", {})
#         print(models)
#     else:
#         print("Error fetching models.")
#         app.state.MODELS = {}

openai.api_type = "azure"
openai.api_key = AZURE_OPENAI_API_KEY
openai.api_base = AZURE_OPENAI_BASE_URL
openai.api_version = AZURE_OPENAI_API_VERSION
openai.deployment_name = AZURE_OPENAI_DEPLOYMENT_NAME

async def get_raw_models(id: Optional[str] = None):
    try:
        response = openai.Model.list(id=id)
        # print("Raw response from API:", response)  # Debugging statement
        models = response.get("data", [])
        # print("Parsed models:", models)  # Debugging statement
        return models
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []


def merge_models_lists(model_lists):
    merged_list = []
    
    for idx, models in enumerate(model_lists):
        if models and "error" not in models:
            filtered_models = [
                {
                    **model,
                    "name": model.get("name", model["id"]),
                    "owned_by": "openai",
                    "openai": model,
                    "urlIdx": idx,
                }
                for model in models
                if model["id"] and any(
                    keyword in model["id"]
                    for keyword in ["babbage", "dall-e", "davinci", "embedding", "tts", "whisper"]
                )
            ]
            merged_list.extend(filtered_models)
    
    return merged_list


async def get_all_models(raw=False) -> dict[str, list] | list:
    response = await get_raw_models()
    if raw:
        return response

    # Ensure response is a list
    model_lists = [response] if isinstance(response, list) else []
    
    # Filter and merge models
    models = {"data": merge_models_lists(model_lists)}
    app.state.MODELS = {model["id"]: model for model in models["data"]}

    return models


@app.get("/models")
async def get_models(url_idx: Optional[int] = None, user=Depends(get_verified_user)):
    models = await get_all_models()
    return app.state.MODELS

class MessageContent(BaseModel):
    type: str  # 'text' or 'image'
    data: str  # text for 'text' type or base64 encoded image for 'image' type

class ChatCompletionRequest(BaseModel):
    messages: List[Dict[str, Union[str, MessageContent]]]
    max_tokens: Optional[int] = 100
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stream: Optional[bool] = False

@app.post("/chat/completions")
async def generate_chat_completion(
    form_data: ChatCompletionRequest,
    user=Depends(get_verified_user),
):
    url = f"{AZURE_OPENAI_BASE_URL}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
    headers = {
        "api-key": AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json",
    }

    # Process messages to handle text and image content
    processed_messages = []
    for message in form_data.messages:
        content_type = message["content"].type  # Access type directly as an attribute
        content_data = message["content"].data  # Access data directly as an attribute

        if content_type == "text":
            processed_messages.append({
                "role": message["role"],
                "content": content_data
            })
        elif content_type == "image":
            # Images are marked with placeholder data for processing
            processed_messages.append({
                "role": message["role"],
                "content": f"[IMAGE DATA: {content_data[:50]}...]"  # Short preview of image data
            })

    # Build the request body with allowed parameters
    body = {
        "messages": processed_messages,
        "max_tokens": form_data.max_tokens,
        "temperature": form_data.temperature,
        "top_p": form_data.top_p,
        "frequency_penalty": form_data.frequency_penalty,
        "presence_penalty": form_data.presence_penalty,
        "stream": form_data.stream
    }

    # Filter body to allowed parameters
    allowed_params = {
        "messages", "temperature", "max_tokens", "presence_penalty", "frequency_penalty",
        "top_p", "stream"
    }
    filtered_body = {k: v for k, v in body.items() if k in allowed_params}

    try:
        response = requests.post(url, json=filtered_body, headers=headers, stream=form_data.stream)

        response.raise_for_status()
        
        # Handle streaming responses
        if form_data.stream:
            return StreamingResponse(response.iter_lines(), media_type="application/json")
        else:
            return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
