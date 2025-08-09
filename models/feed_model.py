from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field
from sqlalchemy import Index, String, TIMESTAMP, Text, ForeignKey
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.article_model import ArticleEntity

from .base import Base


class FeedEntity(Base):
    __tablename__ = 'feeds'
    __table_args__ = (
        Index('feeds_url_index', 'url'),
    )

    id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)

    # Relations
    user_id: Mapped[int] = mapped_column(BIGINT(20), ForeignKey('users.id'))
    theme_id: Mapped[Optional[int]] = mapped_column(BIGINT(20), ForeignKey('themes.id'), nullable=True)

    # Données du flux
    title: Mapped[Optional[str]] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(1024))
    description: Mapped[Optional[str]] = mapped_column(Text)
    favicon: Mapped[Optional[str]] = mapped_column(String(512))

    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    # ORM relationships (lazy, optional backrefs)
    # articles = relationship('ArticleEntity', back_populates='feed', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'theme_id': self.theme_id,
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'favicon': self.favicon,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


# Pydantic schemas
class FeedBase(BaseModel):
    user_id: int
    theme_id: Optional[int] = None
    title: Optional[str] = None
    url: str
    description: Optional[str] = None
    favicon: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FeedCreate(BaseModel):
    user_id: int
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    favicon: Optional[str] = None
    theme_id: Optional[int] = None


class FeedUpdate(BaseModel):
    user_id: Optional[int] = None
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    favicon: Optional[str] = None
    theme_id: Optional[int] = None


class ArticleInFeedInput(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    publication_date: Optional[datetime] = None


class FeedDataAND_ARTICLE(BaseModel):
    user_id: int
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    favicon: Optional[str] = None
    theme_id: Optional[int] = None
    articles: List[ArticleInFeedInput] = Field(default_factory=list)



class FeedResponse(FeedBase):
    id: int

    class Config:
        from_attributes = True
