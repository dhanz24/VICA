import os
import sys


from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import aiohttp
import httpx


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from VICA.apps.VICA.routes.auth import router as auth_router
from VICA.apps.VICA.routes.user import router as user_router
from VICA.apps.VICA.routes.chat import router as chat_router



app = FastAPI(
    title="VICA Backend",
    docs_url="/docs",
)


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

# To use from pdf2image import convert_from_bytes, install poppler-utils (https://pdf2image.readthedocs.io/en/latest/installation.html)
