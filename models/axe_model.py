import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Union, Annotated

from fastapi import UploadFile, File
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, text, ForeignKey
from sqlalchemy.dialects.mysql import BIGINT, DOUBLE, INTEGER, LONGTEXT, MEDIUMTEXT, TINYINT, YEAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from utils.database import Base

from sqlalchemy import Date, DateTime, Enum, ForeignKeyConstraint, Index, String, TIMESTAMP, Text, Time, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import decimal


# Définir le modèle de données
class AxeEntity(Base):
    __tablename__ = 'axes'
    __table_args__ = (
        Index('axes_name_unique', 'name', unique=True),
    )

    id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    icon: Mapped[Optional[str]] = mapped_column(String(255))
    color: Mapped[Optional[str]] = mapped_column(String(255))
    theme_id: Mapped[int] = mapped_column(BIGINT(20), ForeignKey('themes.id'))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'color': self.color,
            'theme_id': self.theme_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    
class AxeBase(BaseModel):
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None
    theme_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    

class AxeCreateBase(BaseModel):
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None
    theme_id: int


class AxeUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    theme_id: Optional[int] = None    

class AxeResponse(AxeBase):
    id: int
    
    class Config:
        from_attributes = True


