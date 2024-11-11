import uuid
import os
import sys
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, Boolean, DateTime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from VICA.apps.VICA.config.database import Base, get_db

####################
# User DB Schema
####################

class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    role = Column(String)
    profile_image_url = Column(Text)
    active = Column(Boolean)
    last_active_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserModel(BaseModel):
    id: str
    name: Optional[str]
    email: Optional[str]
    password: Optional[str]
    role: Optional[str]
    profile_image_url: Optional[str]
    active: Optional[bool]
    last_active_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

####################
# Forms
####################

class UserRoleUpdateForm(BaseModel):
    id: str
    role: str

class UserUpdateForm(BaseModel):
    name: str
    email: str
    profile_image_url: str
    password: Optional[str] = None

####################

class UserTable:
    def insert_new_user(
        self,
        id: str,
        name: str,
        email: str,
        password: str,
        role: str = "user",
        profile_image_url: str = "/user.png",
        active: bool = True,
        last_active_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> Optional[UserModel]:
        with get_db() as db:
            user_data = {
                "id": id,
                "name": name,
                "email": email,
                "password": password,
                "role": role,
                "profile_image_url": profile_image_url,
                "active": active,
                "last_active_at": last_active_at or datetime.utcnow(),
                "created_at": created_at or datetime.utcnow(),
                "updated_at": updated_at or datetime.utcnow(),
            }
            user = UserModel(**user_data)
            result = User(**user.model_dump())
            db.add(result)
            db.commit()
            db.refresh(result)
            return user

    def get_users(self, skip: int = 0, limit: int = 50) -> list[UserModel]:
        with get_db() as db:
            users = db.query(User).all()
            return [UserModel.model_validate(user) for user in users]

    def get_user_by_id(self, id: str) -> Optional[UserModel]:
        with get_db() as db:
            user = db.query(User).filter(User.id == id).first()
            if user:
                return UserModel.model_validate(user)
            else:
                return None
            
    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        with get_db() as db:
            user = db.query(User).filter(User.email == email).first()
        if user:
            return UserModel.model_validate(user.__dict__)
        else:
            return None

    def get_num_users(self) -> int:
        with get_db() as db:
            return db.query(User).count()

    def update_user_role(self, id: str, role: str) -> Optional[UserModel]:
        with get_db() as db:
            user = db.query(User).filter(User.id == id).first()
            if user:
                user.role = role
                user.updated_at = datetime.utcnow()
                db.commit()
                return UserModel.model_validate(user)
            else:
                return None

    def update_user(self, id: str, form_data: UserUpdateForm) -> Optional[UserModel]:
        with get_db() as db:
            user = db.query(User).filter(User.id == id).first()
            if user:
                user.name = form_data.name
                user.email = form_data.email
                user.profile_image_url = form_data.profile_image_url
                if form_data.password:
                    user.password = form_data.password
                user.updated_at = datetime.utcnow()
                db.commit()
                return UserModel.model_validate(user)
            else:
                return None

    def delete_user(self, id: str) -> bool:
        with get_db() as db:
            user = db.query(User).filter(User.id == id).first()
            if user:
                db.delete(user)
                db.commit()
                return True
            else:
                return False

    def update_user_last_active_by_id(self, id: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                db.query(User).filter_by(id=id).update(
                    {"last_active_at": datetime.utcnow()}
                )
                db.commit()

                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def update_user_role_by_id(self, id: str, role: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                db.query(User).filter_by(id=id).update({"role": role})
                db.commit()
                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

Users = UserTable()