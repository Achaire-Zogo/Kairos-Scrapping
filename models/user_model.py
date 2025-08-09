import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Union, Annotated

from fastapi import UploadFile, File
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, text
from sqlalchemy.dialects.mysql import BIGINT, DOUBLE, INTEGER, LONGTEXT, MEDIUMTEXT, TINYINT, YEAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .base import Base

from sqlalchemy import Date, DateTime, Enum, ForeignKeyConstraint, Index, String, TIMESTAMP, Text, Time, text
from sqlalchemy.dialects.mysql import BIGINT, DOUBLE, INTEGER, LONGTEXT, MEDIUMTEXT, TINYINT, YEAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import decimal


# Définir le modèle de données
class UserEntity(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('users_email_unique', 'email', unique=True),
    )

    id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(Enum('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'), server_default=text("'0'"))
    status: Mapped[str] = mapped_column(Enum('active', 'inactive'), server_default=text("'active'"))
    password: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[Optional[str]] = mapped_column(String(255))
    profile_image: Mapped[Optional[str]] = mapped_column(String(255))
    color: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'type': self.type,
            'status': self.status,
            'password': self.password,
            'phone_number': self.phone_number,
            'profile_image': self.profile_image,
            'color': self.color,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    
class UserBase(BaseModel):
    name: str
    email: str
    type: str
    status: str
    password: str
    phone_number: Optional[str] = None
    profile_image: Optional[str] = None
    color: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    

class UserCreateBase(BaseModel):
    name: str
    email: EmailStr
    password: str
    type: str = "0"
    status: str = "active"
    phone_number: Optional[str] = None
    color: Optional[str] = None
    
class UserCreate(UserCreateBase):
    profile_image: Optional[UploadFile] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    type: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None
    profile_image: Optional[UploadFile] = None
    color: Optional[str] = None
    

class UserLogin(BaseModel):
    email: str
    password: str

class UserAuthorization(BaseModel):
    token: str

class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True

