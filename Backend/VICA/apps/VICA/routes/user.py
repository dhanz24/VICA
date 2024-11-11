import os
import sys
import json
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.responses import JSONResponse 
from fastapi.encoders import jsonable_encoder 
from pydantic import BaseModel 
from datetime import datetime, timedelta, timezone
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from VICA.apps.VICA.models.user import Users, UserModel
from VICA.apps.VICA.models.auth import (
    SigninResponse,
    SignupForm,
    SigninForm,
)
from VICA.apps.VICA.utils.auth import get_password_hash, validate_email_format

router = APIRouter()


####################
# Add User

@router.post("/add", response_model=SigninResponse)
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
        datetimenow = (datetime.now(timezone(timedelta(hours=7)))).timestamp()  # Indonesian Western Standard Time (WIB)
        
        user = Users.insert_new_user(
            id=id,
            name=form_data.name,
            email=form_data.email,
            password=hashed_password,
            role=role,
            profile_image_url=form_data.profile_image_url,
            active=False,
            last_active_at=int(datetimenow),
            created_at=int(datetimenow),
            updated_at=int(datetimenow),
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
# Get All Users

@router.get("/getUser", response_model=List[UserModel])
async def get_all_users(request: Request, response: Response):
    users = Users.get_all_users()
    return users

####################
# Get User By ID

@router.get("/getUser/{id}", response_model=UserModel)
async def get_user_by_id(request: Request, response: Response, id: str):
    user = Users.get_user_by_id(id)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found.")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 