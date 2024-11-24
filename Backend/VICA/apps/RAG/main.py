import os
import sys
import json
import uuid
import datetime
import logging

from groq import Groq
import cohere

from typing import Optional
from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import Response

from llama_index.core import Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from VICA.apps.VICA.models.user import Users

from VICA.apps.RAG.rag import RAGService
from VICA.apps.RAG.pdf import PDFService

from Backend.VICA.config import (
    LLM_MODEL_NAME,
    EMBED_MODEL_NAME,
    COHERE_API_KEY,
    GROQ_API_KEY,
)

from VICA.apps.VICA.utils.constanta import ERROR_MESSAGES

from VICA.apps.VICA.utils.auth import (
    get_verified_user,
    get_admin_user,
    verify_password,
    validate_email_format
    )

app = FastAPI(
    title="RAG",
    docs_url="/docs",
)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


############  
# RAG ROUTES
############       

class AskQuestionDTO(BaseModel):
    question: str

class RAGRouter:
    def __init__(self, app: FastAPI, rag_service: RAGService) -> None:
        self.app = app
        self.rag_service = rag_service
        self.register_routes()

    def register_routes(self):
        @self.app.post("/pdf/describe")
        async def describe_pdf(file: UploadFile) -> JSONResponse:
            description = await self.rag_service.pdf_service.describe_pdf(file)

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "PDF description retrieved successfully",
                    "description": description,
                },
            )

        @self.app.post("/knowledge/create")
        async def create_knowledge_base(
            user = Depends(get_verified_user),
            chat_id: str = Form(...),
            file: UploadFile = File(...),
        ) -> JSONResponse:

            user_id = user.id
            
            await self.rag_service.create_knowledge_base(user_id, chat_id, file)

            return JSONResponse(
                status_code=201,
                content={
                    "status": "success",
                    "message": "Knowledge base created successfully for chat",
                    "chat_id": chat_id,
                },
            )

        @self.app.post("/knowledge/query/{chat_id}")
        def ask_question(body: AskQuestionDTO, chat_id : str, user = Depends(get_verified_user)) -> JSONResponse:
            result = self.rag_service.execute_query(
                user.id , chat_id, body.question
            )
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Query executed successfully",
                    "result": result.response,
                },
            )


###########
# Instansiasi semua dependency
###########

llm = Ollama(model=LLM_MODEL_NAME, request_timeout=120)
embed_model = OllamaEmbedding(model_name=EMBED_MODEL_NAME)
co = cohere.Client(COHERE_API_KEY)

Settings.llm = llm
Settings.embed_model = embed_model

pdf_service = PDFService(Groq(api_key=GROQ_API_KEY))
rag_service = RAGService(llm, embed_model, co, pdf_service)

# Instansiasi RAGRouter dan daftarkan rute ke FastAPI
RAGRouter(app, rag_service)