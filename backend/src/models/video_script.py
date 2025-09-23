from sqlalchemy import Column, String, Text, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base


class FormatTypeEnum(enum.Enum):
    conversational = "conversational"
    monologue = "monologue"


class InputSourceEnum(enum.Enum):
    generated = "generated"
    manual_subject = "manual_subject"
    manual_script = "manual_script"


class VideoScript(Base):
    __tablename__ = "video_scripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("generated_themes.id"), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    estimated_duration = Column(Integer, nullable=False)  # seconds
    format_type = Column(Enum(FormatTypeEnum), nullable=False, default=FormatTypeEnum.conversational)
    speaker_count = Column(Integer, nullable=False, default=2)
    input_source = Column(Enum(InputSourceEnum), nullable=False)
    manual_input = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    theme = relationship("GeneratedTheme", back_populates="scripts")
    project = relationship("VideoProject", back_populates="script", uselist=False)

    def __repr__(self):
        return f"<VideoScript(title={self.title[:30]}, duration={self.estimated_duration}s)>"