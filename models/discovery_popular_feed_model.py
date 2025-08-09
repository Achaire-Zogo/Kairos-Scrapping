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
class DiscoveryPopularFeedEntity(Base):
    __tablename__ = 'discovery_popular_feed'
    __table_args__ = (
        Index('discovery_popular_feed_url_unique', 'url', unique=True),
    )

    id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url, 
            'description': self.description,
            'category': self.category,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    
class DiscoveryPopularFeedBase(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    

class DiscoveryPopularFeedCreateBase(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    category: Optional[str] = None    

class DiscoveryPopularFeedUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    

class DiscoveryPopularFeedResponse(DiscoveryPopularFeedBase):
    id: int
    
    class Config:
        from_attributes = True 

