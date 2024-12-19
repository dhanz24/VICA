from fastapi import APIRouter, UploadFile, Form, File, Depends
from fastapi.responses import JSONResponse
from Backend.VICA.apps.VICA.services.rag import RAGService
from Backend.VICA.apps.VICA.dto.chat import AskQuestionDTO


class ChatRouter:
    def __init__(self, rag_service: RAGService = File(...)) -> None:
        self.router = APIRouter()
        self.rag_service = rag_service

        @self.router.post("/pdf/describe")
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

        @self.router.post("/knowledge/create")
        async def create_knowledge_base(
            user_id: str = Form(...),
            chat_id: str = Form(...),
            file: UploadFile = File(...),
            include_visuals: bool = Form(True),
        ) -> JSONResponse:
            await self.rag_service.create_knowledge_base(
                user_id, chat_id, file, include_visuals
            )

            return JSONResponse(
                status_code=201,
                content={
                    "status": "success",
                    "message": "Knowledge base created successfully for chat",
                    "chat_id": chat_id,
                },
            )

        @self.router.post("/knowledge/query")
        def ask_question(body: AskQuestionDTO) -> JSONResponse:
            result = self.rag_service.execute_query(
                body.user_id, body.chat_id, body.question
            )
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Query executed successfully",
                    "result": result.response,
                },
            )
