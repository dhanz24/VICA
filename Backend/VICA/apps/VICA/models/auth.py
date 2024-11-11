import os
import sys
import json

from pydantic import BaseModel
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

class Token(BaseModel):
    token: str
    token_type: str

class ApiKey(BaseModel):
    api_key: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    profile_image_url: str

class SigninResponse(Token, UserResponse):
    pass

class SigninForm(BaseModel):
    email: str
    password: str

class UpdatePasswordForm(BaseModel):
    password: str
    new_password: str

class SignupForm(BaseModel):
    name: str
    email: str
    password: str
    profile_image_url: Optional[str]

class AddUserForm(SignupForm):
    role: Optional[str] = "user"