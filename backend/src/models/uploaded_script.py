from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base


class ValidationStatusEnum(enum.Enum):
    PENDING = "PENDING"
    VALID = "VALID"
    INVALID = "INVALID"


class UploadedScript(Base):
    __tablename__ = "uploaded_scripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # For future user system integration
    workflow_id = Column(UUID(as_uuid=True), nullable=False)  # Links to workflow
    content = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=True)
    content_type = Column(String(50), nullable=False, default='text/plain')
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    validation_status = Column(Enum(ValidationStatusEnum), nullable=False, default=ValidationStatusEnum.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to generation plans
    generation_plans = relationship("GenerationPlan", back_populates="script")

    def __repr__(self):
        return f"<UploadedScript(id={self.id}, workflow_id={self.workflow_id}, status={self.validation_status.value})>"

    @property
    def content_length(self) -> int:
        """Get the length of the script content in characters"""
        return len(self.content) if self.content else 0

    def is_valid(self) -> bool:
        """Check if the uploaded script is valid"""
        return self.validation_status == ValidationStatusEnum.VALID

    def validate_content(self) -> tuple[bool, list[str]]:
        """Validate script content and return (is_valid, errors)"""
        errors = []

        if not self.content or not self.content.strip():
            errors.append("Script content cannot be empty")

        if self.content_length > 51200:  # 50KB limit
            errors.append(f"Script content exceeds 50KB limit (current: {self.content_length} characters)")

        if self.content_type not in ['text/plain', 'text/markdown', 'text/txt']:
            errors.append(f"Invalid content type: {self.content_type}")

        # Check for potentially harmful content (basic check)
        if self.content and any(pattern in self.content.lower() for pattern in ['<script', '<?php', '#!/bin/']):
            errors.append("Script content contains potentially harmful code")

        is_valid = len(errors) == 0
        if is_valid:
            self.validation_status = ValidationStatusEnum.VALID
        else:
            self.validation_status = ValidationStatusEnum.INVALID

        return is_valid, errors