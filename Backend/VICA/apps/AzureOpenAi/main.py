import os
import sys
import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

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

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

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

# @app.middleware("http")
# async def check_url(request: Request, call_next):
#     if len(app.state.MODELS) == 0:
#         await get_models()
#     response = await call_next(request)
#     return response

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

# Initialize OpenAI Instance
openai.api_type = "azure"
openai.api_key = AZURE_OPENAI_API_KEY
openai.api_base = AZURE_OPENAI_BASE_URL
openai.api_version = AZURE_OPENAI_API_VERSION
openai.deployment_name = AZURE_OPENAI_DEPLOYMENT_NAME

async def fetch_raw_models(id: Optional[str] = None):
    try:
        response = openai.Model.list(id=id)
        models = response.get("data", [])
        return models
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch models")


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
                if model["id"] and model["id"] in [  #filter model Azure Openai mana saja yang bisa digunakan pada VICA
                    "gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-35-turbo"
                    ]
            ]
            merged_list.extend(filtered_models)
    
    return merged_list


async def get_all_models(raw=False) -> dict[str, list] | list:
    response = await fetch_raw_models()
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

@app.get("/models/raw")
async def get_raw_models(user=Depends(get_verified_user)):
    models = await get_all_models(raw=True)
    return models

@app.post("/chat/completions")
@app.post("/chat/completions/{url_idx}")
async def generate_chat_completion(
    form_data: dict,
    url_idx: Optional[int] = None,
    user=Depends(get_verified_user),
):

    payload = {**form_data}

    if "metadata" in payload:
        del payload["metadata"]

    model_id = form_data.get("model")

    if not app.state.MODELS:
        await get_all_models()  # Memastikan bahwa app.state.MODELS terisi

    if model_id not in app.state.MODELS:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    # model_info = Models.get_model_by_id(model_id)    #Custom Model Cooming soon jika terdapat 
    # if model_info:
    #     if model_info.base_model_id:
    #         payload["model"] = model_info.base_model_id
    #         params = model_info.params.model_dump()
    #         payload = apply_model_params_to_body_openai(params, payload)
    #         payload = apply_model_system_prompt_to_body(params, payload, user)

    
    model = app.state.MODELS[payload.get("model")]
    idx = model["urlIdx"]

    url = f"{AZURE_OPENAI_BASE_URL}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
    key = AZURE_OPENAI_API_KEY

    if "api.openai.com" not in url and not payload["model"].lower().startswith("o1-"):
        if "max_completion_tokens" in payload:
            # Remove "max_completion_tokens" from the payload
            payload["max_tokens"] = payload["max_completion_tokens"]
            del payload["max_completion_tokens"]
    else:
        if "max_tokens" in payload and "max_completion_tokens" in payload:
            del payload["max_tokens"]

    # Convert the modified body back to JSON
    payload = json.dumps(payload)

    log.debug(payload)
    print(payload)

    headers = {}
    headers["api-key"] = key
    headers["Content-Type"] = "application/json"

    r = None
    session = None
    streaming = False
    response = None

    try:
        session = aiohttp.ClientSession(
            trust_env=True, timeout=aiohttp.ClientTimeout(total=30)
        )
        r = await session.request(
            method = "POST",
            url = url,
            data = payload,
            headers = headers,
        )

# Check if response is SSE
        if "text/event-stream" in r.headers.get("Content-Type", ""):
            streaming = True
            return StreamingResponse(
                r.content,
                status_code=r.status,
                headers=dict(r.headers),
                background=BackgroundTask(
                    cleanup_response, response=r, session=session
                ),
            )
        else:
            try:
                response = await r.json()
            except Exception as e:
                log.error(e)
                response = await r.text()

            r.raise_for_status()
            return response
    except Exception as e:
        log.exception(e)
        error_detail = "VICA: Server Connection Error"
        if isinstance(response, dict):
            if "error" in response:
                error_detail = f"{response['error']['message'] if 'message' in response['error'] else response['error']}"
        elif isinstance(response, str):
            error_detail = response

        raise HTTPException(status_code=r.status if r else 500, detail=error_detail)
    finally:
        if not streaming and session:
            if r:
                r.close()
            await session.close()

