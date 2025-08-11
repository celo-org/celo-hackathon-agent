"""
Configuration module for the API server.
"""

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from pydantic import RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from root .env file
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """API server settings."""

    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "GitHub Repository Analyzer API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./analyzer_db.sqlite")

    # Redis settings
    REDIS_URL: RedisDsn = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Security settings
    SECRET_KEY: str = os.getenv("JWT_SECRET", "supersecretkey")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRATION", "60"))

    # IPFS settings
    IPFS_URL: str = os.getenv("IPFS_URL", "/dns/localhost/tcp/5001")
    IPFS_GATEWAY: str = os.getenv("IPFS_GATEWAY", "https://ipfs.io/ipfs/")

    # LLM settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))

    # GitHub settings
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # CORS settings
    CORS_ORIGINS: list = ["*"]
    CORS_ORIGINS_REGEX: str = ""

    # Metadata for API docs
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = """
    GitHub Repository Analyzer API allows you to analyze GitHub repositories using LLMs,
    generate detailed reports, and store them on IPFS.
    """
    CONTACT_NAME: str = "API Support"
    CONTACT_EMAIL: str = "support@example.com"

    # Model config
    model_config = SettingsConfigDict(
        case_sensitive=True,
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: Any) -> Any:
        """Ensure DATABASE_URL is properly formatted."""
        if isinstance(v, str):
            return v
        return str(v)

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: Any) -> Any:
        """Ensure REDIS_URL is properly formatted."""
        if isinstance(v, str):
            return v
        return str(v)

    def get_config(self) -> Dict[str, Any]:
        """Get all configuration values as a dictionary."""
        return {
            "database_url": self.DATABASE_URL,
            "redis_url": self.REDIS_URL,
            "google_api_key": self.GOOGLE_API_KEY,
            "model": self.DEFAULT_MODEL,
            "temperature": self.TEMPERATURE,
            "log_level": self.LOG_LEVEL,
            "ipfs_url": self.IPFS_URL,
            "ipfs_gateway": self.IPFS_GATEWAY,
            "github_token": self.GITHUB_TOKEN,
        }


# Create a global settings object
settings = Settings()
