"""
Configuration management for BlackRoad Operator.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Operator configuration loaded from environment variables."""

    # API Keys
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    salesforce_username: str = Field(default="", alias="SALESFORCE_USERNAME")
    salesforce_password: str = Field(default="", alias="SALESFORCE_PASSWORD")
    salesforce_token: str = Field(default="", alias="SALESFORCE_TOKEN")

    # Pi Cluster Endpoints
    hailo_endpoint: str = Field(default="http://octavia.local:8080", alias="HAILO_ENDPOINT")
    lucidia_endpoint: str = Field(default="http://lucidia.local:8080", alias="LUCIDIA_ENDPOINT")
    aria_endpoint: str = Field(default="http://aria.local:8080", alias="ARIA_ENDPOINT")
    alice_endpoint: str = Field(default="http://alice.local:8080", alias="ALICE_ENDPOINT")

    # Service Configuration
    default_model: str = Field(default="claude-sonnet-4-20250514", alias="DEFAULT_MODEL")
    fallback_model: str = Field(default="gpt-4", alias="FALLBACK_MODEL")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    timeout_seconds: int = Field(default=30, alias="TIMEOUT_SECONDS")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    audit_log_path: str = Field(default="/var/log/blackroad/audit.jsonl", alias="AUDIT_LOG_PATH")

    # Redis (for caching/state)
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
