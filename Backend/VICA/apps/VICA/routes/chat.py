import os
import sys
import json
import uuid
import datetime
import logging

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from VICA.apps.VICA.models.user import Users

from VICA.apps.VICA.utils.constanta import ERROR_MESSAGES
from VICA.apps.VICA.models.chat import (
    ChatForm,
    ChatResponse,
    Chats,
    ChatTitleIdResponse,
)

from VICA.apps.VICA.utils.auth import (
    get_verified_user,
    get_admin_user,
    verify_password,
    validate_email_format
    )

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

router = APIRouter()

CORS_ALLOW_ORIGIN = os.getenv("CORS_ALLOW_ORIGIN", "*")

############################
# GetChatList
############################

@router.get("/", response_model=list[ChatTitleIdResponse])
@router.get("/list", response_model=list[ChatTitleIdResponse])
async def get_session_user_chat_list(
    user=Depends(get_verified_user), page: Optional[int] = None
):
    if page is not None:
        limit = 60
        skip = (page - 1) * limit

        return Chats.get_chat_title_id_list_by_user_id(user.id, skip=skip, limit=limit)
    else:
        return Chats.get_chat_title_id_list_by_user_id(user.id)


############################
# DeleteAllChats
############################

@router.delete("/", response_model=bool)
async def delete_all_user_chats(request: Request, user=Depends(get_verified_user)):
    if (
        user.role == "user"
        and not request.app.state.config.USER_PERMISSIONS["chat"]["deletion"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    result = Chats.delete_chats_by_user_id(user.id)
    return result

############################
# GetUserChatList
############################

@router.get("/list/user/{user_id}", response_model=list[ChatTitleIdResponse])
async def get_user_chat_list_by_user_id(
    user_id: str,
    user=Depends(get_admin_user),
    skip: int = 0,
    limit: int = 50,
):
    return Chats.get_chat_list_by_user_id(
        user_id, include_archived=True, skip=skip, limit=limit
    )

############################
# CreateNewChat
############################

@router.post("/new", response_model=Optional[ChatResponse])
async def create_new_chat(form_data: ChatForm, user=Depends(get_verified_user)):
    try:
        chat = Chats.insert_new_chat(user.id, form_data)
        return ChatResponse(**{**chat.model_dump(), "chat": json.loads(chat.chat)})
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.DEFAULT()
        )

############################
# GetChats
############################

@router.get("/all", response_model=list[ChatResponse])
async def get_user_chats(user=Depends(get_verified_user)):
    return [
        ChatResponse(**{**chat.model_dump(), "chat": json.loads(chat.chat)})
        for chat in Chats.get_chats_by_user_id(user.id)
    ]

############################
# GetAllChatsInDB
############################

@router.get("/all/db", response_model=list[ChatResponse])
async def get_all_user_chats_in_db(user=Depends(get_admin_user)):
    if not ENABLE_ADMIN_EXPORT:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    return [
        ChatResponse(**{**chat.model_dump(), "chat": json.loads(chat.chat)})
        for chat in Chats.get_chats()
    ]

############################
# GetChatById
############################

@router.get("/{id}", response_model=Optional[ChatResponse])
async def get_chat_by_id(id: str, user=Depends(get_verified_user)):
    chat = Chats.get_chat_by_id_and_user_id(id, user.id)

    if chat:
        return ChatResponse(**{**chat.model_dump(), "chat": json.loads(chat.chat)})
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=ERROR_MESSAGES.NOT_FOUND
        )

############################
# UpdateChatById
############################


@router.post("/{id}", response_model=Optional[ChatResponse])
async def update_chat_by_id(
    id: str, form_data: ChatForm, user=Depends(get_verified_user)
):
    chat = Chats.get_chat_by_id_and_user_id(id, user.id)
    if chat:
        updated_chat = {**json.loads(chat.chat), **form_data.chat}
        
        # Panggil update dan pastikan kembalian tidak None
        chat = Chats.update_chat_by_id(id, updated_chat)
        if chat is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Update failed."
            )
        
        return ChatResponse(**{**chat.model_dump(), "chat": json.loads(chat.chat)})
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )



############################
# DeleteChatById
############################


@router.delete("/{id}", response_model=bool)
async def delete_chat_by_id(request: Request, id: str, user=Depends(get_verified_user)):
    if user.role == "admin":
        result = Chats.delete_chat_by_id(id)
        return result
    else:
        if not request.app.state.config.USER_PERMISSIONS["chat"]["deletion"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
            )

        result = Chats.delete_chat_by_id_and_user_id(id, user.id)
        return result

############################
# ArchiveChat
############################


@router.get("/{id}/archive", response_model=Optional[ChatResponse])
async def archive_chat_by_id(id: str, user=Depends(get_verified_user)):
    chat = Chats.get_chat_by_id_and_user_id(id, user.id)
    if chat:
        chat = Chats.toggle_chat_archive_by_id(id)
        return ChatResponse(**{**chat.model_dump(), "chat": json.loads(chat.chat)})
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=ERROR_MESSAGES.DEFAULT()
        )
        
