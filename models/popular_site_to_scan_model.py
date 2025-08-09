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
class PopularSiteToScanEntity(Base):
    __tablename__ = 'popular_site_to_scan'
    __table_args__ = (
        Index('popular_site_to_scan_url_unique', 'url', unique=True),
    )

    id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(255))
    logo: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'logo': self.logo,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    
class PopularSiteToScanBase(BaseModel):
    name: str
    url: str
    logo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    

class PopularSiteToScanCreateBase(BaseModel):
    name: str
    url: str
    logo: Optional[str] = None
    
class PopularSiteToScanCreate(PopularSiteToScanCreateBase):
    logo: Optional[str] = None

class PopularSiteToScanUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    logo: Optional[str] = None
    

class PopularSiteToScanResponse(PopularSiteToScanBase):
    id: int
    
    class Config:
        from_attributes = True 

