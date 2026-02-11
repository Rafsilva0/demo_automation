"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Salesforce
    salesforce_username: str
    salesforce_password: str
    salesforce_security_token: str
    salesforce_domain: str = "login"

    # Ada
    ada_api_key: str
    ada_api_base_url: str = "https://api.ada.cx/v1"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_temperature: float = 0.7

    # Slack
    slack_webhook_url: str
    slack_channel: str = "#sc-team"

    # Application
    log_level: str = "INFO"
    environment: Literal["development", "staging", "production"] = "development"

    # Webhook security
    webhook_secret: str | None = None

    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
