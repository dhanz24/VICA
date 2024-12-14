import os
import sys
import json
import logging
from typing import Optional, Union
from pydantic import BaseModel
import aiohttp
import httpx
from dotenv import load_dotenv
from sqlalchemy import text

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from VICA.apps.ollama.main import app as ollama_app 
from VICA.apps.AzureOpenAi.main import app as azure_openai_app
from VICA.apps.Groq.main import app as groq_app
from VICA.apps.RAG.main import app as rag_app

from VICA.apps.VICA.config.database import Session
from VICA.apps.VICA.main import app as vica_app

from chainlit.utils import mount_chainlit

app = FastAPI(
    title="VICA Backend",
    docs_url="/docs",
)

# Mount another FastAPI app

app.mount("/ollama", ollama_app)
app.mount("/azure-openai", azure_openai_app)
app.mount("/groq", groq_app)
app.mount("/rag", rag_app)

app.mount("/vica", vica_app)

@app.get("/chat")
def start_chat():
    return {"message": "Chat application is running at /chainlit"}

# Mount Chainlit app
mount_chainlit(app=app, target="Frontend/chainlit/main.py", path="/chainlit")

@app.get("/health")
async def health_check():
    return {"status": True}

@app.get("/health/db")
async def health_check_db():
    Session.execute(text("SELECT 1;")).all()
    return {"status": True}

# Run this file with: 
# uvicorn Backend.VICA.main:app --port 8000 --host 0.0.0.0 --reload
