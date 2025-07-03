from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, text
from sqlalchemy.dialects.mysql import BIGINT, DOUBLE, INTEGER, LONGTEXT, MEDIUMTEXT, TINYINT, YEAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from utils.database import Base

from sqlalchemy import Date, DateTime, Enum, ForeignKeyConstraint, Index, String, TIMESTAMP, Text, Time, text
from sqlalchemy.dialects.mysql import BIGINT, DOUBLE, INTEGER, LONGTEXT, MEDIUMTEXT, TINYINT, YEAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Définir le modèle de données
class ThemeEntity(Base):
    __tablename__ = 'themes'
    __table_args__ = (
        Index('themes_name_unique', 'name', unique=True),
    )

    id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    
class ThemeBase(BaseModel):
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    

class ThemeCreateBase(BaseModel):
    name: str
    

class ThemeUpdate(BaseModel):
    name: Optional[str] = None
    

class ThemeResponse(ThemeBase):
    id: int
    
    class Config:
        from_attributes = True

