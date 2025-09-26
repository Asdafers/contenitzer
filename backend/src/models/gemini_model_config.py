"""
GeminiModelConfig model for runtime configuration of model selection and fallback behavior.
"""

import os
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Index, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import validates
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from .base import Base


class GeminiModelConfig(Base):
    """
    Runtime configuration for Gemini model selection and fallback behavior.
    
    Provides configurable model selection, retry logic, and fallback mechanisms
    for the GeminiService to ensure robust image generation operations.
    """
    __tablename__ = "gemini_model_configs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Model configuration
    primary_model = Column(String(100), nullable=False, default="gemini-2.5-flash-image")
    fallback_model = Column(String(100), nullable=False, default="gemini-pro")

    # Retry configuration
    max_retries = Column(Integer, nullable=False, default=3)
    retry_delay_ms = Column(Integer, nullable=False, default=1000)

    # Feature flags
    model_availability_check = Column(Boolean, nullable=False, default=True)

    # Configuration metadata
    configuration_name = Column(String(100), nullable=False, default="default")
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Performance tracking
    usage_stats = Column(JSON, default=dict)  # Track usage patterns and performance
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_gemini_config_active', 'is_active'),
        Index('idx_gemini_config_name', 'configuration_name'),
        Index('idx_gemini_config_primary_model', 'primary_model'),
        Index('idx_gemini_config_fallback_model', 'fallback_model'),
        Index('idx_gemini_config_last_used', 'last_used'),
    )

    def __repr__(self) -> str:
        return f"<GeminiModelConfig(name={self.configuration_name}, primary={self.primary_model}, fallback={self.fallback_model})>"

    @validates('primary_model', 'fallback_model')
    def validate_model_names(self, key: str, model_name: str) -> str:
        """Validate that model names are non-empty and follow Gemini naming convention."""
        if not model_name or not model_name.strip():
            raise ValueError(f"{key} cannot be empty")
        
        model_name = model_name.strip()
        
        if not model_name.startswith('gemini-'):
            raise ValueError(f"{key} must start with 'gemini-' (got: {model_name})")
        
        return model_name

    @validates('max_retries')
    def validate_max_retries(self, key: str, max_retries: int) -> int:
        """Validate that max_retries is between 1 and 10."""
        if max_retries < 1 or max_retries > 10:
            raise ValueError("max_retries must be between 1 and 10")
        return max_retries

    @validates('retry_delay_ms')
    def validate_retry_delay(self, key: str, retry_delay_ms: int) -> int:
        """Validate that retry_delay_ms is between 100 and 10000."""
        if retry_delay_ms < 100 or retry_delay_ms > 10000:
            raise ValueError("retry_delay_ms must be between 100 and 10000")
        return retry_delay_ms

    @validates('configuration_name')
    def validate_configuration_name(self, key: str, name: str) -> str:
        """Validate that configuration_name is non-empty and reasonable length."""
        if not name or not name.strip():
            raise ValueError("configuration_name cannot be empty")
        
        name = name.strip()
        if len(name) > 100:
            raise ValueError("configuration_name cannot exceed 100 characters")
        
        return name

    def validate_model_differences(self) -> None:
        """Validate that primary and fallback models are different."""
        if self.primary_model == self.fallback_model:
            raise ValueError("Primary and fallback models must be different")

    def get_active_configuration(self) -> Dict[str, Any]:
        """
        Get the current active configuration as a dictionary.
        
        Returns:
            Dictionary containing all configuration parameters
        """
        return {
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "max_retries": self.max_retries,
            "retry_delay_ms": self.retry_delay_ms,
            "model_availability_check": self.model_availability_check,
            "configuration_name": self.configuration_name,
            "is_active": self.is_active
        }

    def update_settings(self, **kwargs) -> None:
        """
        Update configuration settings.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        updatable_fields = {
            'primary_model', 'fallback_model', 'max_retries', 
            'retry_delay_ms', 'model_availability_check', 
            'description', 'is_active'
        }
        
        for key, value in kwargs.items():
            if key in updatable_fields:
                setattr(self, key, value)
        
        # Validate after updates
        self.validate_model_differences()
        self.updated_at = datetime.utcnow()

    def record_usage(self, model_used: str, success: bool, response_time_ms: Optional[float] = None) -> None:
        """
        Record usage statistics for performance tracking.
        
        Args:
            model_used: The model that was actually used
            success: Whether the operation was successful
            response_time_ms: Response time in milliseconds
        """
        if not self.usage_stats:
            self.usage_stats = {}
        
        # Initialize model stats if not exists
        if model_used not in self.usage_stats:
            self.usage_stats[model_used] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_response_time_ms": 0.0,
                "average_response_time_ms": 0.0
            }
        
        stats = self.usage_stats[model_used]
        stats["total_requests"] += 1
        
        if success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1
        
        if response_time_ms is not None:
            stats["total_response_time_ms"] += response_time_ms
            stats["average_response_time_ms"] = stats["total_response_time_ms"] / stats["total_requests"]
        
        self.last_used = datetime.utcnow()

    def get_success_rate(self, model_name: Optional[str] = None) -> float:
        """
        Get success rate for a specific model or overall.
        
        Args:
            model_name: Specific model to get success rate for, or None for overall
            
        Returns:
            Success rate as a float between 0.0 and 1.0
        """
        if not self.usage_stats:
            return 0.0
        
        if model_name:
            if model_name not in self.usage_stats:
                return 0.0
            stats = self.usage_stats[model_name]
            total = stats.get("total_requests", 0)
            if total == 0:
                return 0.0
            return stats.get("successful_requests", 0) / total
        else:
            # Overall success rate
            total_requests = sum(stats.get("total_requests", 0) for stats in self.usage_stats.values())
            successful_requests = sum(stats.get("successful_requests", 0) for stats in self.usage_stats.values())
            if total_requests == 0:
                return 0.0
            return successful_requests / total_requests

    def should_use_fallback(self) -> bool:
        """
        Determine if fallback model should be used based on primary model performance.
        
        Returns:
            True if fallback should be used, False otherwise
        """
        if not self.model_availability_check:
            return False
        
        primary_success_rate = self.get_success_rate(self.primary_model)
        
        # Use fallback if primary model has low success rate (< 50%)
        return primary_success_rate < 0.5 and primary_success_rate > 0.0

    @classmethod
    def load_from_environment(cls) -> 'GeminiModelConfig':
        """
        Create a configuration instance from environment variables.
        
        Returns:
            GeminiModelConfig instance with values from environment
        """
        return cls(
            primary_model=os.getenv("GEMINI_PRIMARY_MODEL", "gemini-2.5-flash-image"),
            fallback_model=os.getenv("GEMINI_FALLBACK_MODEL", "gemini-pro"),
            max_retries=int(os.getenv("GEMINI_MAX_RETRIES", "3")),
            retry_delay_ms=int(os.getenv("GEMINI_RETRY_DELAY_MS", "1000")),
            model_availability_check=os.getenv("GEMINI_AVAILABILITY_CHECK", "true").lower() == "true",
            configuration_name=os.getenv("GEMINI_CONFIG_NAME", "default"),
            description=os.getenv("GEMINI_CONFIG_DESCRIPTION", "Default Gemini model configuration")
        )

    @classmethod
    def get_default_config(cls) -> 'GeminiModelConfig':
        """
        Get the default configuration.
        
        Returns:
            GeminiModelConfig instance with default values
        """
        return cls(
            primary_model="gemini-2.5-flash-image",
            fallback_model="gemini-pro",
            max_retries=3,
            retry_delay_ms=1000,
            model_availability_check=True,
            configuration_name="default",
            description="Default Gemini model configuration"
        )


# Event listeners for validation
@event.listens_for(GeminiModelConfig, 'before_insert')
@event.listens_for(GeminiModelConfig, 'before_update')
def validate_before_save(mapper, connection, target):
    """Validate model configuration before saving to database."""
    target.validate_model_differences()