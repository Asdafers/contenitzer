from sqlalchemy import Column, String, Text, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base


class ExtractionMethodEnum(enum.Enum):
    automated = "automated"
    manual = "manual"


class GeneratedTheme(Base):
    __tablename__ = "generated_themes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trending_content_id = Column(UUID(as_uuid=True), ForeignKey("trending_content.id"), nullable=False)
    theme_name = Column(String(100), nullable=False)
    theme_description = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=False)  # 0.0-1.0
    extraction_method = Column(Enum(ExtractionMethodEnum), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    trending_content = relationship("TrendingContent", back_populates="themes")
    scripts = relationship("VideoScript", back_populates="theme")

    def __repr__(self):
        return f"<GeneratedTheme(name={self.theme_name}, score={self.relevance_score})>"