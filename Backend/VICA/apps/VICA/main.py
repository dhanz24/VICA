import os
import sys
from groq import Groq
import cohere
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from llama_index.core import Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import aiohttp
import httpx


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from VICA.apps.VICA.routes.auth import router as auth_router
from VICA.apps.VICA.routes.user import router as user_router
from VICA.apps.VICA.routes.chat import router as chat_router

from Backend.VICA.apps.VICA.services.rag import RAGService
from Backend.VICA.apps.VICA.services.pdf import PDFService
from Backend.VICA.apps.VICA.routes.chat import ChatRouter
from Backend.VICA.config import (
    LLM_MODEL_NAME,
    EMBED_MODEL_NAME,
    COHERE_API_KEY,
    GROQ_API_KEY,
)

app = FastAPI(
    title="VICA Backend",
    docs_url="/docs",
)

llm = Ollama(model=LLM_MODEL_NAME, request_timeout=120)
embed_model = OllamaEmbedding(model_name=EMBED_MODEL_NAME)
co = cohere.Client(COHERE_API_KEY)

Settings.llm = llm
Settings.embed_model = embed_model

pdf_service = PDFService(Groq(api_key=GROQ_API_KEY))
rag_service = RAGService(llm, embed_model, co, pdf_service)
chat_router = ChatRouter(rag_service)


# Include router
app.include_router(auth_router, prefix="/auths", tags=["Auths"])
app.include_router(user_router, prefix="/users", tags=["Users"]),
app.include_router(chat_router, prefix="/chats", tags=["Chats"]),


# Global ValueError Handler
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"status": "error", "msg": str(exc)})


@app.get("/")
async def get_status():
    return {"status": True}


# Usage: uvicorn Backend.VICA.apps.VICA.main:app
# To use from pdf2image import convert_from_bytes, install poppler-utils (https://pdf2image.readthedocs.io/en/latest/installation.html)
