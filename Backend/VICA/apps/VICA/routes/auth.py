import os
import sys
import json
import uuid
import datetime

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
from VICA.apps.VICA.models.auth import (
    SigninResponse,
    SignupForm,
    SigninForm,
)
from VICA.apps.VICA.utils.auth import (
    get_password_hash, 
    verify_password,
    validate_email_format, 
    create_token
    )


router = APIRouter()

####################
# Signup User

@router.post("/signup", response_model=SigninResponse)
async def signup(request: Request, response: Response, form_data: SignupForm):
    
    if not form_data.email or not form_data.password or form_data.email == "" or form_data.password == "":
        raise HTTPException(status_code=400, detail="Email and password are required.") 

    if not validate_email_format(form_data.email):
        raise HTTPException(status_code=400, detail="Invalid email format.")

    if Users.get_user_by_email(form_data.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    try:
        role = (
            "admin" if Users.get_num_users() == 0 else "user"
        )

        id = str(uuid.uuid4())
        hashed_password = get_password_hash(form_data.password)
        
        user = Users.insert_new_user(
            id=id,
            name=form_data.name,
            email=form_data.email,
            password=hashed_password,
            role=role,
            profile_image_url=form_data.profile_image_url,
            active=True,
            last_active_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ) 
    
        if user:
            print("User registered successfully.")
            token = create_token(
                data={
                    "id": user.id,
                    "name": user.name,
                },
                expires_delta=timedelta(days=3),
            )

            # Set the cookie token
            response.set_cookie(
                key="token",
                value=token,
                httponly=True,  # Ensures the cookie is not accessible via JavaScript
            )
            
            return {
                "token": token,
                "token_type": "bearer",
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_image_url": user.profile_image_url,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to register user.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

####################
# Signin User

@router.post("/signin", response_model=SigninResponse)
async def signin(request: Request, response: Response, form_data: SigninForm):
    
    if not form_data.email or not form_data.password or form_data.email == "" or form_data.password == "":
        raise HTTPException(status_code=400, detail="Email and password are required.") 

    if not validate_email_format(form_data.email):
        raise HTTPException(status_code=400, detail="Invalid email format.")

    user = Users.get_user_by_email(form_data.email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found.")

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid password.")

    try:
        token = create_token(
            data={
                "id": user.id,
                "name": user.name,
            },
            expires_delta=timedelta(days=3),
        )

        # Set the cookie token
        response.set_cookie(
            key="token",
            value=token,
            httponly=True,  # Ensures the cookie is not accessible via JavaScript
        )

        return {
            "token": token,
            "token_type": "bearer",
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "profile_image_url": user.profile_image_url,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
