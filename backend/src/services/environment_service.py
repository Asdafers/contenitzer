"""
Environment validation service for setup configuration
"""

import os
from typing import Dict, List, Any, Tuple
from urllib.parse import urlparse
from ..models.configuration_profile import ConfigurationProfile


class EnvironmentValidationService:
    """Service for validating environment configuration"""

    def __init__(self):
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[str] = []

    def validate_configuration(self, config: ConfigurationProfile) -> Tuple[bool, List[Dict[str, str]], List[str]]:
        """
        Validate complete configuration profile
        Returns: (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            # Validate Redis configuration
            self._validate_redis_config(config)

            # Validate API keys
            self._validate_api_keys(config)

            # Validate service URLs
            self._validate_service_urls(config)

            return len(self.errors) == 0, self.errors, self.warnings

        except Exception as e:
            self.errors.append({
                "field": "general",
                "message": f"Validation error: {str(e)}",
                "severity": "error"
            })
            return False, self.errors, self.warnings

    def _validate_redis_config(self, config: ConfigurationProfile) -> None:
        """Validate Redis configuration"""
        try:
            parsed = urlparse(config.redis_url)
            if not parsed.hostname:
                self._add_error("redis_url", "Redis URL must include hostname")
        except Exception:
            self._add_error("redis_url", "Invalid Redis URL format")

        # Check database number conflicts
        if config.redis_session_db == config.redis_task_db:
            self._add_warning("Redis session and task databases are the same - may cause conflicts")

    def _validate_api_keys(self, config: ConfigurationProfile) -> None:
        """Validate API keys"""
        placeholders = ["your_key_here", "YOUR_API_KEY", "placeholder"]

        if config.youtube_api_key in placeholders:
            self._add_error("youtube_api_key", "YouTube API key is a placeholder value")

        if config.openai_api_key in placeholders:
            self._add_error("openai_api_key", "OpenAI API key is a placeholder value")

    def _validate_service_urls(self, config: ConfigurationProfile) -> None:
        """Validate service URLs"""
        urls_to_check = [
            ("backend_url", config.backend_url),
            ("frontend_url", config.frontend_url),
            ("websocket_url", config.websocket_url)
        ]

        for field_name, url in urls_to_check:
            if url:
                try:
                    parsed = urlparse(url)
                    if not parsed.hostname:
                        self._add_error(field_name, f"{field_name} must include hostname")
                except Exception:
                    self._add_error(field_name, f"Invalid {field_name} format")

    def _add_error(self, field: str, message: str) -> None:
        """Add validation error"""
        self.errors.append({
            "field": field,
            "message": message,
            "severity": "error"
        })

    def _add_warning(self, message: str) -> None:
        """Add validation warning"""
        self.warnings.append(message)