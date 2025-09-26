#!/usr/bin/env python3
"""
Environment Configuration Validation Script
Validates .env file configuration for Content Creator Workbench
"""

import os
import sys
import urllib.parse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class EnvironmentValidator:
    """Validates environment configuration for the application"""

    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file or "backend/.env"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.config: Dict[str, str] = {}

    def load_env_file(self) -> bool:
        """Load environment variables from .env file"""
        env_path = Path(self.env_file)

        if not env_path.exists():
            self.errors.append(f"Environment file not found: {env_path}")
            return False

        try:
            with open(env_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        self.config[key] = value
                    else:
                        self.warnings.append(f"Line {line_num}: Invalid format '{line}'")

        except Exception as e:
            self.errors.append(f"Failed to read {env_path}: {e}")
            return False

        return True

    def validate_redis_config(self) -> None:
        """Validate Redis configuration"""
        redis_url = self.config.get('REDIS_URL', '')

        if not redis_url:
            self.errors.append("REDIS_URL is required")
            return

        # Validate Redis URL format
        try:
            parsed = urllib.parse.urlparse(redis_url)
            if parsed.scheme not in ['redis', 'rediss']:
                self.errors.append(f"REDIS_URL must use redis:// or rediss:// scheme, got: {parsed.scheme}")
            if not parsed.hostname:
                self.errors.append("REDIS_URL must include hostname")
            if parsed.port and (parsed.port < 1 or parsed.port > 65535):
                self.errors.append(f"REDIS_URL port must be 1-65535, got: {parsed.port}")
        except Exception as e:
            self.errors.append(f"Invalid REDIS_URL format: {e}")

        # Validate Redis database numbers
        for db_key in ['REDIS_SESSION_DB', 'REDIS_TASK_DB']:
            db_value = self.config.get(db_key)
            if db_value:
                try:
                    db_num = int(db_value)
                    if db_num < 0 or db_num > 15:
                        self.errors.append(f"{db_key} must be 0-15, got: {db_num}")
                except ValueError:
                    self.errors.append(f"{db_key} must be an integer, got: {db_value}")

    def validate_api_keys(self) -> None:
        """Validate API keys"""
        required_keys = ['YOUTUBE_API_KEY', 'GEMINI_API_KEY']

        for key in required_keys:
            value = self.config.get(key, '')
            if not value:
                self.errors.append(f"{key} is required")
            elif len(value) < 10:  # Basic length check
                self.warnings.append(f"{key} seems too short (less than 10 characters)")
            elif value in ['your_key_here', 'YOUR_API_KEY', 'placeholder']:
                self.errors.append(f"{key} contains placeholder value: {value}")

    def validate_gemini_model_config(self) -> None:
        """Validate Gemini model configuration"""
        model = self.config.get('GEMINI_IMAGE_MODEL', 'gemini-2.5-flash-image')

        # List of valid Gemini models for image generation
        valid_models = [
            'gemini-2.5-flash-image',
            'gemini-pro',
            'gemini-pro-vision'
        ]

        if model not in valid_models:
            self.warnings.append(f"GEMINI_IMAGE_MODEL '{model}' may not be supported. Valid options: {', '.join(valid_models)}")

        # Recommend using the latest model
        if model != 'gemini-2.5-flash-image':
            self.warnings.append(f"Consider using 'gemini-2.5-flash-image' for best image generation performance")

        # Check for placeholder values
        placeholder_values = ['your_model_here', 'REPLACE_WITH_MODEL']
        if model in placeholder_values:
            self.errors.append(f"GEMINI_IMAGE_MODEL contains placeholder value: {model}")

    def validate_service_urls(self) -> None:
        """Validate service URLs"""
        url_fields = {
            'BACKEND_URL': 'http://localhost:8000',
            'FRONTEND_URL': 'http://localhost:3000',
            'WEBSOCKET_URL': 'ws://localhost:8000/ws'
        }

        for field, default in url_fields.items():
            url = self.config.get(field, default)

            try:
                parsed = urllib.parse.urlparse(url)

                if field == 'WEBSOCKET_URL':
                    if parsed.scheme not in ['ws', 'wss']:
                        self.errors.append(f"{field} must use ws:// or wss:// scheme")
                else:
                    if parsed.scheme not in ['http', 'https']:
                        self.errors.append(f"{field} must use http:// or https:// scheme")

                if not parsed.hostname:
                    self.errors.append(f"{field} must include hostname")

            except Exception as e:
                self.errors.append(f"Invalid {field} format: {e}")

    def validate_environment_type(self) -> None:
        """Validate environment type"""
        env_type = self.config.get('ENVIRONMENT', 'local')

        valid_environments = ['local', 'docker', 'cloud', 'development', 'staging', 'production']

        if env_type not in valid_environments:
            self.warnings.append(f"Unknown ENVIRONMENT value: {env_type}. Valid options: {', '.join(valid_environments)}")

    def validate_optional_settings(self) -> None:
        """Validate optional configuration settings"""
        # Debug mode
        debug = self.config.get('DEBUG', 'true').lower()
        if debug not in ['true', 'false', '1', '0']:
            self.warnings.append(f"DEBUG should be true/false, got: {debug}")

        # Log level
        log_level = self.config.get('LOG_LEVEL', 'INFO').upper()
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_levels:
            self.warnings.append(f"LOG_LEVEL should be one of {valid_levels}, got: {log_level}")

    def check_missing_recommended(self) -> None:
        """Check for missing recommended settings"""
        recommended = {
            'DEBUG': 'true',
            'LOG_LEVEL': 'INFO',
            'ENVIRONMENT': 'local',
            'GEMINI_IMAGE_MODEL': 'gemini-2.5-flash-image'
        }

        for key, default in recommended.items():
            if key not in self.config:
                self.warnings.append(f"Recommended setting missing: {key}={default}")

    def validate(self) -> bool:
        """Run all validations"""
        print(f"🔍 Validating environment configuration: {self.env_file}")

        if not self.load_env_file():
            return False

        # Run all validation checks
        self.validate_redis_config()
        self.validate_api_keys()
        self.validate_gemini_model_config()
        self.validate_service_urls()
        self.validate_environment_type()
        self.validate_optional_settings()
        self.check_missing_recommended()

        return len(self.errors) == 0

    def report_results(self) -> None:
        """Print validation results"""
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ Environment configuration is valid!")
        elif not self.errors:
            print(f"\n✅ Environment configuration is valid (with {len(self.warnings)} warnings)")
        else:
            print(f"\n❌ Environment configuration has {len(self.errors)} errors and {len(self.warnings)} warnings")

    def generate_template(self, output_path: str = "backend/.env.example") -> None:
        """Generate example environment file"""
        template = """# Content Creator Workbench Environment Configuration
# Copy this file to .env and update with your actual values

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_DB=1
REDIS_TASK_DB=2

# API Keys (replace with your actual keys)
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Gemini Model Configuration
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image

# Service URLs (defaults for local development)
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
WEBSOCKET_URL=ws://localhost:8000/ws

# Environment Settings
ENVIRONMENT=local
DEBUG=true
LOG_LEVEL=INFO

# Optional: Database URL (if not using Redis for everything)
# DATABASE_URL=sqlite:///./content_creator.db

# Optional: Security settings
# SECRET_KEY=your-secret-key-for-jwt-tokens
# SESSION_TIMEOUT_HOURS=24
"""

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(template)

        print(f"📝 Generated environment template: {output_path}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate environment configuration")
    parser.add_argument('--env-file', default='backend/.env', help='Path to .env file')
    parser.add_argument('--generate-template', action='store_true', help='Generate .env.example file')
    parser.add_argument('--template-output', default='backend/.env.example', help='Output path for template')

    args = parser.parse_args()

    validator = EnvironmentValidator(args.env_file)

    if args.generate_template:
        validator.generate_template(args.template_output)
        return

    success = validator.validate()
    validator.report_results()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()