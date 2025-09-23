from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from .base import Base


class ContentCategory(Base):
    __tablename__ = "content_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    youtube_category_id = Column(String(50), nullable=False)
    popularity_rank = Column(Integer, nullable=False)  # 1-5, with 1 being most popular
    last_analyzed = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    trending_content = relationship("TrendingContent", back_populates="category")

    def __repr__(self):
        return f"<ContentCategory(name={self.name}, rank={self.popularity_rank})>"