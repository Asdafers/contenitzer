#!/usr/bin/env python3
"""
Environment file template generator
Creates .env files with appropriate defaults for different environments
"""

import os
import argparse
from pathlib import Path
from typing import Dict, Any


class EnvTemplateGenerator:
    """Generates environment file templates"""

    def __init__(self):
        self.templates = {
            "local": self._local_template,
            "docker": self._docker_template,
            "production": self._production_template
        }

    def _local_template(self) -> Dict[str, Any]:
        """Template for local development"""
        return {
            "# Content Creator Workbench - Local Development Environment": "",
            "": "",
            "# Redis Configuration": "",
            "REDIS_URL": "redis://localhost:6379/0",
            "REDIS_SESSION_DB": "1",
            "REDIS_TASK_DB": "2",
            "": "",
            "# API Keys (replace with your actual keys)": "",
            "YOUTUBE_API_KEY": "your_youtube_api_key_here",
            "GEMINI_API_KEY": "your_gemini_api_key_here",
            "": "",
            "# Service URLs": "",
            "BACKEND_URL": "http://localhost:8000",
            "FRONTEND_URL": "http://localhost:3000",
            "WEBSOCKET_URL": "ws://localhost:8000/ws",
            "": "",
            "# Development Settings": "",
            "ENVIRONMENT": "local",
            "DEBUG": "true",
            "LOG_LEVEL": "INFO",
            "": "",
            "# Optional Database": "",
            "# DATABASE_URL": "sqlite:///./content_creator.db"
        }

    def _docker_template(self) -> Dict[str, Any]:
        """Template for Docker development"""
        return {
            "# Content Creator Workbench - Docker Environment": "",
            "": "",
            "# Redis Configuration (Docker service names)": "",
            "REDIS_URL": "redis://redis:6379/0",
            "REDIS_SESSION_DB": "1",
            "REDIS_TASK_DB": "2",
            "": "",
            "# API Keys": "",
            "YOUTUBE_API_KEY": "your_youtube_api_key_here",
            "GEMINI_API_KEY": "your_gemini_api_key_here",
            "": "",
            "# Service URLs (Docker internal)": "",
            "BACKEND_URL": "http://backend:8000",
            "FRONTEND_URL": "http://frontend:3000",
            "WEBSOCKET_URL": "ws://backend:8000/ws",
            "": "",
            "# Docker Settings": "",
            "ENVIRONMENT": "docker",
            "DEBUG": "true",
            "LOG_LEVEL": "INFO"
        }

    def _production_template(self) -> Dict[str, Any]:
        """Template for production environment"""
        return {
            "# Content Creator Workbench - Production Environment": "",
            "# WARNING: Update all placeholder values before deployment": "",
            "": "",
            "# Redis Configuration": "",
            "REDIS_URL": "rediss://your-redis-host:6380/0",
            "REDIS_SESSION_DB": "1",
            "REDIS_TASK_DB": "2",
            "": "",
            "# API Keys (REQUIRED)": "",
            "YOUTUBE_API_KEY": "REPLACE_WITH_ACTUAL_KEY",
            "GEMINI_API_KEY": "REPLACE_WITH_ACTUAL_KEY",
            "": "",
            "# Service URLs": "",
            "BACKEND_URL": "https://your-backend-domain.com",
            "FRONTEND_URL": "https://your-frontend-domain.com",
            "WEBSOCKET_URL": "wss://your-backend-domain.com/ws",
            "": "",
            "# Production Settings": "",
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "LOG_LEVEL": "WARNING",
            "": "",
            "# Security": "",
            "SECRET_KEY": "GENERATE_STRONG_SECRET_KEY",
            "SESSION_TIMEOUT_HOURS": "24"
        }

    def generate_template(self, env_type: str, output_path: str) -> None:
        """Generate environment template file"""
        if env_type not in self.templates:
            raise ValueError(f"Unknown environment type: {env_type}")

        template = self.templates[env_type]()

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            for key, value in template.items():
                if key.startswith("#") or key == "":
                    f.write(f"{key}\n")
                else:
                    f.write(f"{key}={value}\n")

        print(f"✅ Generated {env_type} environment template: {output_path}")

    def validate_existing_env(self, env_path: str) -> Dict[str, Any]:
        """Validate existing .env file"""
        if not Path(env_path).exists():
            return {"valid": False, "error": "File not found"}

        try:
            env_vars = {}
            with open(env_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

            # Check for required variables
            required = ["REDIS_URL", "YOUTUBE_API_KEY", "OPENAI_API_KEY"]
            missing = [var for var in required if var not in env_vars]

            # Check for placeholder values
            placeholders = []
            placeholder_values = ["your_key_here", "REPLACE_WITH_ACTUAL_KEY", "your_youtube_api_key_here"]

            for key, value in env_vars.items():
                if value in placeholder_values:
                    placeholders.append(key)

            return {
                "valid": len(missing) == 0 and len(placeholders) == 0,
                "missing_vars": missing,
                "placeholder_vars": placeholders,
                "total_vars": len(env_vars)
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Generate environment file templates")
    parser.add_argument("--type", choices=["local", "docker", "production"],
                       default="local", help="Environment type")
    parser.add_argument("--output", default="backend/.env.example",
                       help="Output file path")
    parser.add_argument("--validate", help="Validate existing .env file")

    args = parser.parse_args()

    generator = EnvTemplateGenerator()

    if args.validate:
        result = generator.validate_existing_env(args.validate)
        print(f"Validation results for {args.validate}:")

        if result["valid"]:
            print("✅ Environment file is valid")
            print(f"📊 Found {result['total_vars']} environment variables")
        else:
            print("❌ Environment file has issues")

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                if result.get("missing_vars"):
                    print(f"Missing variables: {', '.join(result['missing_vars'])}")
                if result.get("placeholder_vars"):
                    print(f"Placeholder values: {', '.join(result['placeholder_vars'])}")
    else:
        generator.generate_template(args.type, args.output)
        print(f"💡 To validate: python3 {__file__} --validate {args.output}")


if __name__ == "__main__":
    main()