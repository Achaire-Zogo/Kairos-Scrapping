from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Index, String, TIMESTAMP, Text, ForeignKey
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ArticleEntity(Base):
    __tablename__ = 'articles'
    __table_args__ = (
        Index('articles_feed_id_index', 'feed_id'),
        Index('articles_url_index', 'url'),
    )

    id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)

    # Relation
    feed_id: Mapped[int] = mapped_column(BIGINT(20), ForeignKey('feeds.id'))

    # Données de l'article
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(1024))
    description: Mapped[Optional[str]] = mapped_column(Text)
    publication_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    def to_dict(self):
        return {
            'id': self.id,
            'feed_id': self.feed_id,
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'publication_date': self.publication_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


# Pydantic schemas
class ArticleBase(BaseModel):
    feed_id: int
    title: str
    url: str
    description: Optional[str] = None
    publication_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ArticleCreate(BaseModel):
    feed_id: int
    title: str
    url: str
    description: Optional[str] = None
    publication_date: Optional[datetime] = None


class ArticleUpdate(BaseModel):
    feed_id: Optional[int] = None
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    publication_date: Optional[datetime] = None


class ArticleResponse(ArticleBase):
    id: int

    class Config:
        from_attributes = True
