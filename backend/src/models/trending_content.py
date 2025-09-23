from sqlalchemy import Column, String, BigInteger, Integer, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base


class TimeframeEnum(enum.Enum):
    weekly = "weekly"
    monthly = "monthly"


class TrendingContent(Base):
    __tablename__ = "trending_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("content_categories.id"), nullable=False)
    youtube_video_id = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    channel_name = Column(String(100), nullable=False)
    view_count = Column(BigInteger, nullable=False)
    trending_rank = Column(Integer, nullable=False)  # 1-3, top 3 in category
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    timeframe = Column(Enum(TimeframeEnum), nullable=False)
    content_metadata = Column(JSON, default=dict)

    # Relationships
    category = relationship("ContentCategory", back_populates="trending_content")
    themes = relationship("GeneratedTheme", back_populates="trending_content")

    def __repr__(self):
        return f"<TrendingContent(title={self.title[:30]}, rank={self.trending_rank})>"